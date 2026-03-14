/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config) => {
    config.externals.push({
      'react-force-graph-2d': 'react-force-graph-2d'
    })
    return config
  }
}

module.exports = nextConfig
