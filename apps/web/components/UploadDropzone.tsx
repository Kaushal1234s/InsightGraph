'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

interface UploadResponse {
  job_id: string
  status: string
  message: string
}

export default function UploadDropzone() {
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null)
  const [jobStatus, setJobStatus] = useState<any>(null)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return
    
    const file = acceptedFiles[0]
    setUploading(true)
    setUploadResult(null)
    setJobStatus(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://localhost:8000/v1/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result: UploadResponse = await response.json()
      setUploadResult(result)

      // Poll for job status
      pollJobStatus(result.job_id)
      
    } catch (error) {
      console.error('Upload error:', error)
      setUploadResult({
        job_id: '',
        status: 'failed',
        message: error instanceof Error ? error.message : 'Upload failed'
      })
    } finally {
      setUploading(false)
    }
  }, [])

  const pollJobStatus = async (jobId: string) => {
    const poll = async () => {
      try {
        const response = await fetch(`http://localhost:8000/v1/jobs/${jobId}`)
        if (response.ok) {
          const status = await response.json()
          setJobStatus(status)
          
          if (status.status === 'processing') {
            setTimeout(poll, 2000) // Poll every 2 seconds
          }
        }
      } catch (error) {
        console.error('Status poll error:', error)
      }
    }
    
    poll()
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/zip': ['.zip'],
    },
    maxSize: 80 * 1024 * 1024, // 80MB
    multiple: false,
  })

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Upload Files
        </h2>
        
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          
          {uploading ? (
            <div className="space-y-2">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
              <p className="text-gray-600">Uploading and processing...</p>
            </div>
          ) : isDragActive ? (
            <p className="text-primary-600">Drop the file here...</p>
          ) : (
            <div className="space-y-2">
              <div className="text-gray-400">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <p className="text-gray-600">Drag & drop a PDF or ZIP file here</p>
              <p className="text-sm text-gray-500">or click to select (max 80MB)</p>
            </div>
          )}
        </div>
      </div>

      {uploadResult && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Upload Result
          </h3>
          <div className="space-y-2">
            <p><strong>Job ID:</strong> {uploadResult.job_id}</p>
            <p><strong>Status:</strong> {uploadResult.status}</p>
            <p><strong>Message:</strong> {uploadResult.message}</p>
          </div>
        </div>
      )}

      {jobStatus && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Processing Status
          </h3>
          <div className="space-y-2">
            <p><strong>Status:</strong> {jobStatus.status}</p>
            <p><strong>Progress:</strong> {jobStatus.progress}%</p>
            <p><strong>Message:</strong> {jobStatus.message}</p>
            
            {jobStatus.status === 'processing' && (
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${jobStatus.progress}%` }}
                ></div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
