import React, { useState, useEffect } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableRow, Paper, IconButton, TextField, Autocomplete, Chip, Container, Button } from '@mui/material';
import FolderIcon from '@mui/icons-material/Folder';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import { styled } from '@mui/system';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import axiosInstance from "./axiosInstance";

const FolderRow = styled(TableRow)(({ theme }) => ({
  '&:hover': {
    backgroundColor: 'rgba(0, 0, 255, 0.1)',
    borderColor: 'rgba(0, 0, 0, 0.2)',
    boxShadow: '0px 4px 8px rgba(0, 0, 0, 0.2)',
    transition: 'all 0.3s ease-in-out',
  },
  borderBottom: '1px solid rgba(128, 128, 128, 0.3)',
  cursor: 'pointer',
  background: 'linear-gradient(135deg, rgba(173, 216, 230, 0.1), rgba(135, 206, 235, 0.1))',
}));

const FolderTree = ({ data, tagsList, onTagUpdate }) => {
  const [expandedFolders, setExpandedFolders] = useState({});
  const [selectedTags, setSelectedTags] = useState({});

  const handleToggle = (id) => {
    setExpandedFolders((prev) => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const handleTagChange = async (event, newValue, folderId) => {
    setSelectedTags(prevState => ({
      ...prevState,
      [folderId]: newValue
    }));
    await onTagUpdate(folderId, newValue);
  };

  const renderRows = (data, parentId, level = 0) => {
    return Object.entries(data)
      .filter(([id, folder]) => folder.parent_id === parentId)
      .map(([id, folder]) => (
        <React.Fragment key={id}>
          <FolderRow onDoubleClick={() => handleToggle(id)} style={{ paddingLeft: `${level * 20}px`, opacity: 1 - level * 0.3 }}>
            <TableCell>
              <Box display="flex" alignItems="center">
                <IconButton>
                  {expandedFolders[id] ? <FolderOpenIcon style={{ color: 'blue' }} /> : <FolderIcon style={{ color: 'blue' }} />}
                </IconButton>
                <Box>
                  <Typography variant="body1">{folder.name}</Typography>
                  <Typography variant="caption" color="textSecondary">{folder.items_count} items</Typography>
                </Box>
              </Box>
            </TableCell>
            <TableCell>{folder.size} bytes</TableCell>
            <TableCell>{new Date(folder.created_at).toLocaleDateString()}</TableCell>
            <TableCell>
              <Autocomplete
                multiple
                id={`tags-outlined-${id}`}
                options={tagsList}
                getOptionLabel={(option) => option}
                filterSelectedOptions
                value={selectedTags[id] || folder.tags || []}
                onChange={(event, newValue) => handleTagChange(event, newValue, id)}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    variant="outlined"
                    label="Теги"
                    placeholder="Добавить тег"
                  />
                )}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      variant="outlined"
                      label={option}
                      {...getTagProps({ index })}
                      sx={{ backgroundColor: `rgba(0, 0, 255, 0.${(index % 9) + 1})` }}
                    />
                  ))
                }
              />
            </TableCell>
          </FolderRow>
          {expandedFolders[id] && renderRows(data, id, level + 1)}
        </React.Fragment>
      ));
  };

  return (
    <TableContainer component={Paper} sx={{ borderRadius: '16px', overflow: 'hidden', boxShadow: '0px 4px 8px rgba(0, 0, 255, 0.2)' }}>
      <Table>
        <TableBody>
          {renderRows(data, '4d1e465a-e583-44a8-bb95-48a6c29065c1')}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default function FolderManager() {
  const [folderData, setFolderData] = useState(null);
  const [tagsList, setTagsList] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const folderResponse = await axiosInstance.get('/kinescope-folders');
        setFolderData(folderResponse.data.couples);

        const tagsResponse = await axiosInstance.get('/get_unique_tags');
        setTagsList(tagsResponse.data.tags);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
  }, []);

  const handleTagUpdate = async (folderId, tags) => {
    try {
      const response = await axiosInstance.post('/update_tags', { folder_id: folderId, tags });
      setFolderData(prevData => ({
        ...prevData,
        [folderId]: {
          ...prevData[folderId],
          tags: response.data.tags
        }
      }));
    } catch (error) {
      console.error('Error updating tags:', error);
    }
  };

  if (!folderData) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <Container>
      <Box display="flex" justifyContent="center" mb={4} mt={2}>
        <Button variant="contained" color="secondary" onClick={() => navigate('/downloads')} sx={{ mx: 1 }}>Загрузка</Button>
      </Box>
      <FolderTree data={folderData} tagsList={tagsList} onTagUpdate={handleTagUpdate} />
    </Container>
  );
}
