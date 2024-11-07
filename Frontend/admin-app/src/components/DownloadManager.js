import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Container, Box, TextField, Button, Typography, CircularProgress, Paper, Snackbar } from '@mui/material';
import Alert from '@mui/material/Alert';
import { useNavigate } from 'react-router-dom';
import axiosInstance from "./axiosInstance";

const extractFileIdFromUrl = (url) => {
  const regex = /\/d\/([a-zA-Z0-9_-]+)/;
  const match = url.match(regex);
  return match ? match[1] : null;
};

const DownloadManager = () => {
  const [fileUrl, setFileUrl] = useState('');
  const [downloads, setDownloads] = useState([]);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDownloads = async () => {
      try {
        const response = await axiosInstance.get('/downloads/');
        setDownloads(response.data);
      } catch (error) {
        console.error(error);
      }
    };

    fetchDownloads();
  }, []);




  const handleDownload = async () => {
    const fileId = extractFileIdFromUrl(fileUrl);
    if (!fileId) {
      setSnackbar({ open: true, message: 'Invalid Google Drive URL', severity: 'error' });
      return;
    }
    setLoading(true);
    try {
      const response = await axiosInstance.post('/download/', { file_id: fileId });

      setDownloads([...downloads, { ...response.data, download_status: 0, file_url: fileUrl }]);
      setFileUrl('');
      setSnackbar({ open: true, message: 'Download started', severity: 'success' });
    } catch (error) {
      setSnackbar({ open: true, message: error.response?.data?.detail || 'Error occurred', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (fileId) => {
    try {
      await axiosInstance.delete(`/download/${fileId}`);
      setDownloads(downloads.filter(download => download.file_id !== fileId));
      setSnackbar({ open: true, message: 'Download deleted', severity: 'success' });
    } catch (error) {
      console.error(error);
      setSnackbar({ open: true, message: 'Error deleting download', severity: 'error' });
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  return (
    <Container>
            <Box display="flex" justifyContent="center" mb={4} mt={2}>
        <Button variant="contained" color="primary" onClick={() => navigate('/folders')} sx={{ mx: 1 }}>Файлы</Button>
      </Box>
      <Box display="flex" alignItems="center" mt={4}>
        <TextField
          label="Google Drive URL"
          value={fileUrl}
          onChange={(e) => setFileUrl(e.target.value)}
          fullWidth
        />
        <Button
          variant="contained"
          color="primary"
          onClick={handleDownload}
          disabled={loading}
          sx={{ ml: 2 }}
        >
          {loading ? <CircularProgress size={24} /> : "Загрузить"}
        </Button>
      </Box>

      {downloads.map((download, index) => (
        <Paper key={index} sx={{ p: 2, mt: 2 }}>
          <Typography variant="h6">
            <a href={`https://drive.google.com/file/d/${download.file_id}/view`} target="_blank" rel="noopener noreferrer">
              {download.file_name}
            </a>
          </Typography>
          <Typography variant="body1">Тип: {download.file_type}</Typography>
          <Typography variant="body1">Статус: {download.download_status}%</Typography>
          <Button
            variant="contained"
            color="secondary"
            onClick={() => handleDelete(download.file_id)}
            sx={{ mt: 1 }}
          >
            Удалить
          </Button>
        </Paper>
      ))}

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default DownloadManager;

