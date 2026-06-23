import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Threads from './pages/Threads'
import ThreadDetail from './pages/ThreadDetail'
import Tripcodes from './pages/Tripcodes'
import TripProfile from './pages/TripProfile'
import Correlate from './pages/Correlate'
import Archive from './pages/Archive'
import Images from './pages/Images'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="threads" element={<Threads />} />
        <Route path="threads/:id" element={<ThreadDetail />} />
        <Route path="tripcodes" element={<Tripcodes />} />
        <Route path="tripcodes/:trip" element={<TripProfile />} />
        <Route path="correlate" element={<Correlate />} />
        <Route path="archive" element={<Archive />} />
        <Route path="images" element={<Images />} />
      </Route>
    </Routes>
  )
}
