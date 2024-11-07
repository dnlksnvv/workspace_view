import React, { useState, useEffect, useCallback } from 'react';
import {
  Grid,
  Box,
  List,
  ListItem,
  FormControlLabel,
  IconButton,
  TextField,
  Autocomplete,
  Chip,
  Snackbar,
  Alert,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import axiosInstance from '../axiosInstance';
import { styled } from '@mui/system';
import loadLogo from '../MDS_Workspace_load_logo.svg';
import showIcon from './show.svg';
import hideIcon from './hide.svg';

const ChannelItem = React.memo(
  styled(ListItem)(({ theme, checked }) => ({
    border: `1px solid ${checked ? 'rgba(0, 128, 0, 0.3)' : 'rgba(255, 0, 0, 0.3)'}`,
    borderRadius: '8px',
    marginBottom: '8px',
    transition: 'transform 0.2s, all 0.2s',
    backgroundColor: checked ? 'rgba(0, 128, 0, 0.1)' : 'rgba(255, 0, 0, 0.1)',
    transform: checked ? 'scale(1)' : 'scale(0.9)',
    '&:hover': {
      transform: checked ? 'scale(1.05)' : 'scale(0.9)',
    },
    '&:active': {
      transform: checked ? 'scale(1)' : 'scale(0.9)',
    },
  }))
);

const ContainerBox = styled(Box)(({ theme }) => ({
  borderRadius: '8px',
  padding: '16px',
}));

const MenuBox = styled(Box)(({ theme }) => ({
  backgroundColor: theme?.palette?.background?.paper || '#fff',
  padding: '5px',
}));

const ScrollContainer = styled(Box)(({ theme }) => ({
  overflowY: 'auto',
  maxHeight: 'calc(100vh - 100px)',
  position: 'relative',
  '&::before, &::after': {
    content: '""',
    position: 'absolute',
    left: 0,
    right: 0,
    height: '20px',
    pointerEvents: 'none',
  },
  '&::before': {
    top: 0,
    background: `linear-gradient(to bottom, rgba(255, 255, 255, 1), rgba(255, 255, 255, 0))`,
  },
  '&::after': {
    bottom: 0,
    background: `linear-gradient(to top, rgba(255, 255, 255, 1), rgba(255, 255, 255, 0))`,
  },
}));

export default function TelegramChannels() {
  const [loading, setLoading] = useState(true); // Состояние загрузки
  const [channels, setChannels] = useState({});
  const [globalExclude, setGlobalExclude] = useState([]);
  const [tags, setTags] = useState([]);
  const [selectedTags, setSelectedTags] = useState({});
  const [userChannels, setUserChannels] = useState([]);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');
  const [view, setView] = useState('userChannels'); // Для управления видом

  useEffect(() => {
    document.body.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = 'auto';
    };
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [userChannelResponse, channelResponse, tagsResponse] = await Promise.all([
          axiosInstance.post('/telegram_service/log_user_email', {}, { withCredentials: true }),
          axiosInstance.get('/telegram_service/get_channels', { withCredentials: true }),
          axiosInstance.get('/get_unique_tags'),
        ]);

        const userChannelIds = userChannelResponse.data.user_channels;
        setChannels(channelResponse.data.channels);
        setGlobalExclude(channelResponse.data.global_exclude);

        const initialTags = {};
        const userChannels = [];

        Object.entries(channelResponse.data.channels).forEach(([channelId, channel]) => {
          initialTags[channelId] = channel.tags || [];
          if (userChannelIds.includes(channelId)) {
            userChannels.push(channelId);
          }
        });

        setSelectedTags(initialTags);
        setUserChannels(userChannels);

        const sortedTags = tagsResponse.data.tags.sort((a, b) => a.localeCompare(b));
        setTags(sortedTags);
      } catch (error) {
        console.error('Error fetching channels:', error);
      } finally {
        setLoading(false); // Устанавливаем состояние загрузки в false после завершения загрузки данных
      }
    };

    fetchData();
  }, []);

  const handleCheckboxChange = useCallback(
    async (channelId) => {
      const isExcluded = globalExclude.includes(channelId);
      const action = isExcluded ? 'remove' : 'add';

      setGlobalExclude((prevGlobalExclude) => {
        if (action === 'add') {
          return [...prevGlobalExclude, channelId];
        } else {
          return prevGlobalExclude.filter((id) => id !== channelId);
        }
      });

      try {
        const token = localStorage.getItem('token');
        await axiosInstance.post(
          '/telegram_service/update_channel_exclude',
          {
            channel_id: channelId,
            action: action,
          },
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
      } catch (error) {
        setGlobalExclude((prevGlobalExclude) => {
          if (action === 'add') {
            return prevGlobalExclude.filter((id) => id !== channelId);
          } else {
            return [...prevGlobalExclude, channelId];
          }
        });
        setSnackbarMessage('Ошибка при обновлении, попробуйте снова');
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
      }
    },
    [globalExclude]
  );

  const handleTagChange = useCallback(
    async (event, newValue, channelId) => {
      const previousTags = selectedTags[channelId] || [];

      setSelectedTags((prevState) => ({
        ...prevState,
        [channelId]: newValue,
      }));

      try {
        const token = localStorage.getItem('token');
        await axiosInstance.post(
          '/telegram_service/update_channel_tags',
          {
            channel_id: channelId,
            tags: newValue,
          },
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
      } catch (error) {
        setSelectedTags((prevState) => ({
          ...prevState,
          [channelId]: previousTags,
        }));
        setSnackbarMessage('Ошибка при обновлении тегов, попробуйте снова');
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
      }
    },
    [selectedTags]
  );

  const handleUserCheckboxChange = useCallback(
    async (channelId) => {
      const isUserChannel = userChannels.includes(channelId);

      setUserChannels((prevState) =>
        prevState.includes(channelId) ? prevState.filter((id) => id !== channelId) : [...prevState, channelId]
      );

      try {
        await axiosInstance.post(
          '/telegram_service/update_user_channel',
          {
            channel_id: channelId,
            action: isUserChannel ? 'remove' : 'add',
          },
          { withCredentials: true }
        );
      } catch (error) {
        setUserChannels((prevState) =>
          isUserChannel ? [...prevState, channelId] : prevState.filter((id) => id !== channelId)
        );
        setSnackbarMessage('Ошибка при обновлении статуса канала, попробуйте снова');
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
      }
    },
    [userChannels]
  );

  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

  const handleViewChange = (event, newView) => {
    if (newView !== null) {
      setView(newView);
    }
  };

  const sortedChannels = Object.entries(channels).sort((a, b) => {
    const nameA = a[1].name.toLowerCase();
    const nameB = b[1].name.toLowerCase();
    const numA = nameA.match(/\d+$/) ? parseInt(nameA.match(/\d+$/)[0], 10) : 0;
    const numB = nameB.match(/\d+$/) ? parseInt(nameB.match(/\d+$/)[0], 10) : 0;

    if (nameA < nameB) return -1;
    if (nameA > nameB) return 1;

    return numB - numA;
      });

  if (loading) {
    // Отображаем логотип загрузки, пока идет загрузка данных
    return (
      <Box sx={{ height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <img
          src={loadLogo}
          alt="Loading..."
          style={{
            width: '250px',
            height: '250px',
            transform: 'translateY(-25px)', // Поднимает элемент вверх на 25 пикселей
          }}
        />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        pt: { xs: '105px', md: '0' }, // Отступ сверху на маленьких экранах
      }}
    >
      <MenuBox>
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
          <ToggleButtonGroup value={view} exclusive onChange={handleViewChange} aria-label="view">
            <ToggleButton value="allChannels" aria-label="all channels">
              Все каналы
            </ToggleButton>
            <ToggleButton value="userChannels" aria-label="user channels">
              Твои каналы
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </MenuBox>

      <ScrollContainer>
        {view === 'userChannels' ? (
          <ContainerBox>
            <List>
              {sortedChannels
                .filter(([channelId]) => !globalExclude.includes(channelId))
                .map(([channelId, channel]) => (
                  <ChannelItem key={channelId} checked={userChannels.includes(channelId)}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                      <FormControlLabel
                        control={
                          <IconButton
                            onClick={() => handleUserCheckboxChange(channelId)}
                            aria-label="toggle channel visibility"
                          >
                            <img
                              src={userChannels.includes(channelId) ? showIcon : hideIcon}
                              alt={userChannels.includes(channelId) ? 'Show Channel' : 'Hide Channel'}
                              style={{ width: 24, height: 24 }}
                            />
                          </IconButton>
                        }
                        label={channel.name}
                      />
                      <Autocomplete
                        multiple
                        id={`tags-outlined-${channelId}`}
                        options={tags}
                        getOptionLabel={(option) => option}
                        filterSelectedOptions
                        value={selectedTags[channelId] || []}
                        onChange={(event, newValue) => handleTagChange(event, newValue, channelId)}
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
                              sx={{ backgroundColor: `rgba(0, 0, 0, 0.${(index % 9) + 1})` }}
                            />
                          ))
                        }
                      />
                    </Box>
                  </ChannelItem>
                ))}
            </List>
          </ContainerBox>
        ) : (
          <ContainerBox>
            <List>
              {sortedChannels.map(([channelId, channel]) => (
                <ChannelItem key={channelId} checked={!globalExclude.includes(channelId)}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                    <FormControlLabel
                      control={
                        <IconButton
                          onClick={() => handleCheckboxChange(channelId)}
                          aria-label="toggle channel visibility"
                        >
                          <img
                            src={!globalExclude.includes(channelId) ? showIcon : hideIcon}
                            alt={!globalExclude.includes(channelId) ? 'Show Channel' : 'Hide Channel'}
                            style={{ width: 24, height: 24 }}
                          />
                        </IconButton>
                      }
                      label={channel.name}
                    />
                    <Autocomplete
                      multiple
                      id={`tags-outlined-${channelId}`}
                      options={tags}
                      getOptionLabel={(option) => option}
                      filterSelectedOptions
                      value={selectedTags[channelId] || []}
                      onChange={(event, newValue) => handleTagChange(event, newValue, channelId)}
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
                            sx={{ backgroundColor: `rgba(0, 0, 0, 0.${(index % 9) + 1})` }}
                          />
                        ))
                      }
                    />
                  </Box>
                </ChannelItem>
              ))}
            </List>
          </ContainerBox>
        )}
      </ScrollContainer>

      <Snackbar open={snackbarOpen} autoHideDuration={6000} onClose={handleSnackbarClose}>
        <Alert onClose={handleSnackbarClose} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
}