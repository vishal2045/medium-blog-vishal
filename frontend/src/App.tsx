import { Routes, Route } from 'react-router-dom'
import { Box } from '@chakra-ui/react'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Events from './pages/Events'

function App() {
  return (
    <Box minH="100vh" bg="gray.50">
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/events" element={<Events />} />
        </Routes>
      </Layout>
    </Box>
  )
}

export default App