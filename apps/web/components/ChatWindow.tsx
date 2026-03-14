'use client'

import { useState, useRef, useEffect } from 'react'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: Array<{
    documentId: string
    documentName: string
    page?: number
    chunkId: string
  }>
}

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId] = useState(() => `session_${Date.now()}`)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      console.log('Sending request to:', 'http://localhost:8000/v1/ask')
      console.log('Request body:', JSON.stringify({ question: input, session_id: sessionId }))
      
      const response = await fetch('http://localhost:8000/v1/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: input,
          session_id: sessionId,
        }),
      })

      console.log('Response status:', response.status)
      console.log('Response headers:', response.headers)

      if (!response.ok) {
        throw new Error(`Chat request failed: ${response.statusText}`)
      }

      // For debugging, let's get the full response as text first
      const responseText = await response.text()
      console.log('Raw response text:', responseText)
      console.log('Response length:', responseText.length)
      
      // Parse the SSE response
      const lines = responseText.split('\n')
      console.log('Number of lines:', lines.length)
      
      let assistantContent = ''
      let sources: any[] = []
      let foundDataLines = 0
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          foundDataLines++
          console.log('Data line found:', line)
          try {
            const data = JSON.parse(line.slice(6))
            console.log('Parsed data:', data)
            
            if (data.type === 'token') {
              assistantContent += data.content
              console.log('Added content:', data.content)
            } else if (data.type === 'sources') {
              sources = data.sources
              console.log('Found sources:', sources)
            }
          } catch (e) {
            console.error('Error parsing SSE data:', e, 'Line was:', line)
          }
        }
      }
      
      console.log('Total data lines found:', foundDataLines)
      console.log('Final assistant content:', assistantContent)

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: assistantContent || 'No response received',
        timestamp: new Date(),
        sources: sources,
      }

      setMessages(prev => [...prev, assistantMessage])
      
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to get response'}`,
        timestamp: new Date(),
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow h-[600px] flex flex-col">
      <div className="border-b px-6 py-4">
        <h2 className="text-lg font-semibold text-gray-900">Chat</h2>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p>Ask a question about your uploaded documents</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  message.type === 'user'
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-300">
                    <p className="text-xs font-semibold mb-1">Sources:</p>
                    <div className="space-y-1">
                      {message.sources.map((source, idx) => (
                        <div key={idx} className="text-xs">
                          <span className="font-medium">{source.documentName}</span>
                          {source.page && <span> (Page {source.page})</span>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t px-6 py-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  )
}
