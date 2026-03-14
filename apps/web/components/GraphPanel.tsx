'use client'

import { useEffect, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'

interface GraphNode {
  id: string
  name: string
  type: 'document' | 'chunk' | 'entity' | 'topic'
  color?: string
  size?: number
}

interface GraphEdge {
  source: string
  target: string
  type: string
  color?: string
}

interface GraphData {
  nodes: GraphNode[]
  links: GraphEdge[]
}

export default function GraphPanel() {
  const graphRef = useRef<any>()
  const [graphData, setGraphData] = useState<GraphData>({
    nodes: [],
    links: []
  })
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)

  useEffect(() => {
    // Fetch real graph data from API
    const fetchGraphData = async () => {
      try {
        // For now, use mock data - will be replaced with actual API call
        const mockData: GraphData = {
          nodes: [
            { id: 'doc1', name: 'Document 1', type: 'document', color: '#3b82f6', size: 10 },
            { id: 'chunk1', name: 'Chunk 1', type: 'chunk', color: '#10b981', size: 5 },
            { id: 'chunk2', name: 'Chunk 2', type: 'chunk', color: '#10b981', size: 5 },
            { id: 'entity1', name: 'AI', type: 'entity', color: '#f59e0b', size: 7 },
            { id: 'entity2', name: 'Graph', type: 'entity', color: '#f59e0b', size: 7 },
            { id: 'topic1', name: 'Technology', type: 'topic', color: '#ef4444', size: 8 },
          ],
          links: [
            { source: 'doc1', target: 'chunk1', type: 'HAS_CHUNK', color: '#94a3b8' },
            { source: 'doc1', target: 'chunk2', type: 'HAS_CHUNK', color: '#94a3b8' },
            { source: 'chunk1', target: 'entity1', type: 'MENTIONS', color: '#94a3b8' },
            { source: 'chunk2', target: 'entity2', type: 'MENTIONS', color: '#94a3b8' },
            { source: 'chunk1', target: 'topic1', type: 'ABOUT', color: '#94a3b8' },
            { source: 'entity1', target: 'entity2', type: 'RELATES_TO', color: '#94a3b8' },
          ]
        }
        setGraphData(mockData)
      } catch (error) {
        console.error('Error fetching graph data:', error)
      }
    }
    
    fetchGraphData()
  }, [])

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node)
  }

  const getNodeColor = (node: GraphNode) => {
    const colors = {
      document: '#3b82f6',
      chunk: '#10b981',
      entity: '#f59e0b',
      topic: '#ef4444'
    }
    return colors[node.type] || '#6b7280'
  }

  const handleZoomToFit = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow h-[600px] flex flex-col">
      <div className="border-b px-6 py-4 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-900">Knowledge Graph</h2>
        <button
          onClick={handleZoomToFit}
          className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
        >
          Fit to View
        </button>
      </div>

      <div className="flex-1 relative">
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          nodeLabel="name"
          nodeColor={(node: any) => getNodeColor(node)}
          nodeVal={(node: any) => node.size || 5}
          nodeCanvasObject={(node: any, ctx: any, globalScale: any) => {
            const label = node.name
            const fontSize = 12 / globalScale
            ctx.font = `${fontSize}px Sans-Serif`
            ctx.textAlign = 'center'
            ctx.textBaseline = 'middle'
            ctx.fillStyle = getNodeColor(node)
            ctx.beginPath()
            ctx.arc(node.x, node.y, node.size || 5, 0, 2 * Math.PI)
            ctx.fill()
            
            // Draw label
            ctx.fillStyle = '#1f2937'
            ctx.fillText(label, node.x, node.y + (node.size || 5) + 10)
          }}
          linkColor={(link: any) => link.color || '#94a3b8'}
          linkWidth={2}
          onNodeClick={handleNodeClick}
          enableNodeDrag={true}
          enableZoomPanInteraction={true}
          width={undefined}
          height={undefined}
        />
      </div>

      {selectedNode && (
        <div className="border-t px-6 py-4">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="font-semibold text-gray-900">{selectedNode.name}</h3>
              <p className="text-sm text-gray-500">Type: {selectedNode.type}</p>
              <p className="text-sm text-gray-500">ID: {selectedNode.id}</p>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
