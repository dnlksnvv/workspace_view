import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Home from './components/Home';
import SignIn from './components/SignIn';
import SignUp from './components/SignUp';
import ModeratorLecturesToday from './components/ModeratorLecturesToday/ModeratorLecturesToday';
import ModeratorLecturesArchive from './components/ModeratorLecturesToday/ModeratorLecturesArchive';
import DownloadManager from './components/DownloadManager';
import PrivateRoute from './components/PrivateRoute';
import Settings from './components/Settings/Settings';
import Schedule from './components/Settings/Schedule';
import FolderManager from './components/FolderManager';
import StreamsPage from './components/StreamsPage';


function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/signin" />} />
        <Route path="/home" element={
          <PrivateRoute>
            <Home />
          </PrivateRoute>
        } />
        <Route path="/moderator/lectures/today" element={
          <PrivateRoute>
            <ModeratorLecturesToday />
          </PrivateRoute>
        } />
        <Route path="/moderator/lectures/archive" element={
          <PrivateRoute>
            <ModeratorLecturesArchive />
          </PrivateRoute>
        } />
        <Route path="/settings" element={
          <PrivateRoute>
            <Settings />
          </PrivateRoute>
        } />
        <Route path="/downloads" element={
          <PrivateRoute>
            <DownloadManager />
          </PrivateRoute>
        } />
        <Route path="/folders" element={
          <PrivateRoute>
            <FolderManager />
          </PrivateRoute>
        } />
        <Route path="/streams" element={
          <PrivateRoute>
            <StreamsPage />
          </PrivateRoute>
        } />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/schedule" element={<Schedule />} /> {/* Новый маршрут для страницы расписания */}
      </Routes>
    </Router>
  );
}

export default App;
