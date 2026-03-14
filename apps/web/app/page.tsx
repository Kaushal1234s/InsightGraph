'use client'

import { useState } from 'react'
import UploadDropzone from '@/components/UploadDropzone'
import ChatWindow from '@/components/ChatWindow'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'upload' | 'chat'>('upload')
  const [showGraph, setShowGraph] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-gray-900">InsightGraph</h1>
            <div className="flex space-x-4">
              <button
                onClick={() => setActiveTab('upload')}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  activeTab === 'upload'
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-700 hover:text-gray-900'
                }`}
              >
                Upload
              </button>
              <button
                onClick={() => setActiveTab('chat')}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  activeTab === 'chat'
                    ? 'bg-blue-500 text-white'
                    : 'text-gray-700 hover:text-gray-900'
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => setShowGraph(!showGraph)}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  showGraph
                    ? 'bg-green-500 text-white'
                    : 'text-gray-700 hover:text-gray-900'
                }`}
              >
                {showGraph ? 'Hide Graph' : 'Show Graph'}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Panel */}
          <div>
            {activeTab === 'upload' ? (
              <UploadDropzone />
            ) : (
              <ChatWindow />
            )}
          </div>

          {/* Right Panel - Graph Visualization */}
          {showGraph && (
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Knowledge Graph
                </h2>
                <p className="text-gray-600">Interactive graph visualization will appear here.</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
