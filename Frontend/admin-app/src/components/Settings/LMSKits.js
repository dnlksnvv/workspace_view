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

const StreamItem = React.memo(
  styled(ListItem)(({ theme, checked }) => ({
    border: `1px solid ${
      checked ? 'rgba(0, 128, 0, 0.3)' : 'rgba(255, 0, 0, 0.3)'
    }`,
    borderRadius: '8px',
    marginBottom: '8px',
    transition: 'transform 0.2s, all 0.2s',
    backgroundColor: checked
      ? 'rgba(0, 128, 0, 0.1)'
      : 'rgba(255, 0, 0, 0.1)',
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
}));

export default function LMSStreams() {
  const [loading, setLoading] = useState(true); // Состояние загрузки
  const [streams, setStreams] = useState([]);
  const [globalExclude, setGlobalExclude] = useState([]);
  const [tags, setTags] = useState([]);
  const [selectedTags, setSelectedTags] = useState({});
  const [userStreams, setUserStreams] = useState([]);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');
  const [view, setView] = useState('userStreams'); // Для управления видом

  useEffect(() => {
    // Отключаем прокрутку страницы
    document.body.style.overflow = 'hidden';

    // Восстанавливаем прокрутку страницы при размонтировании компонента
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.time('Fetch Streams');
        const [userStreamResponse, streamResponse, tagsResponse] =
          await Promise.all([
            axiosInstance.post(
              '/lk_service/log_user_email',
              {},
              { withCredentials: true }
            ),
            axiosInstance.get('/lk_service/get_streams', {
              withCredentials: true,
            }),
            axiosInstance.get('/get_unique_tags'),
          ]);
        console.timeEnd('Fetch Streams');

        const userStreamIds = userStreamResponse.data.user_streams;
        setGlobalExclude(streamResponse.data.global_exclude);

        const streamEntries = Object.entries(
          streamResponse.data.streams
        ).sort(([idA, streamA], [idB, streamB]) => {
          const nameA = streamA.name.toLowerCase();
          const nameB = streamB.name.toLowerCase();
          const numA = nameA.match(/\d+$/)
            ? parseInt(nameA.match(/\d+$/)[0], 10)
            : 0;
          const numB = nameB.match(/\d+$/)
            ? parseInt(nameB.match(/\d+$/)[0], 10)
            : 0;

          if (nameA < nameB) return -1;
          if (nameA > nameB) return 1;

          return numB - numA;
        });

        const newStreams = streamEntries.map(([streamId, stream]) => ({
          streamId,
          ...stream,
        }));

        setStreams(newStreams);

        const newSelectedTags = {};
        const newUserStreams = [];

        streamEntries.forEach(([streamId, stream]) => {
          newSelectedTags[streamId] = stream.tags || [];
          if (userStreamIds.includes(streamId)) {
            newUserStreams.push(streamId);
          }
        });

        setSelectedTags(newSelectedTags);
        setUserStreams(newUserStreams);

        const sortedTags = tagsResponse.data.tags.sort((a, b) =>
          a.localeCompare(b)
        );
        setTags(sortedTags);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false); // Устанавливаем состояние загрузки в false после завершения загрузки данных
      }
    };

    fetchData();
  }, []);

  const handleCheckboxChange = useCallback(
    async (streamId) => {
      const isExcluded = globalExclude.includes(streamId);
      const action = isExcluded ? 'remove' : 'add';

      setGlobalExclude((prevGlobalExclude) => {
        if (action === 'add') {
          return [...prevGlobalExclude, streamId];
        } else {
          return prevGlobalExclude.filter((id) => id !== streamId);
        }
      });

      try {
        const token = localStorage.getItem('token');
        await axiosInstance.post(
          '/lk_service/update_stream_exclude',
          {
            stream_id: streamId,
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
            return prevGlobalExclude.filter((id) => id !== streamId);
          } else {
            return [...prevGlobalExclude, streamId];
          }
        });
        setSnackbarMessage(
          'Ошибка при обновлении фильтра набора, попробуйте снова'
        );
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
      }
    },
    [globalExclude]
  );

  const handleUserCheckboxChange = useCallback(
    async (streamId) => {
      const isUserStream = userStreams.includes(streamId);

      setUserStreams((prevState) =>
        prevState.includes(streamId)
          ? prevState.filter((id) => id !== streamId)
          : [...prevState, streamId]
      );

      try {
        await axiosInstance.post(
          '/lk_service/update_user_stream',
          {
            stream_id: streamId,
            action: isUserStream ? 'remove' : 'add',
          },
          { withCredentials: true }
        );
      } catch (error) {
        setUserStreams((prevState) =>
          isUserStream
            ? [...prevState, streamId]
            : prevState.filter((id) => id !== streamId)
        );
        setSnackbarMessage(
          'Ошибка при обновлении статуса вашего набора, попробуйте снова'
        );
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
      }
    },
    [userStreams]
  );

  const handleTagChange = useCallback(
    async (event, newValue, streamId) => {
      const previousTags = selectedTags[streamId] || [];

      setSelectedTags((prevState) => ({
        ...prevState,
        [streamId]: newValue,
      }));

      try {
        const token = localStorage.getItem('token');
        await axiosInstance.post(
          '/lk_service/update_stream_tags',
          {
            stream_id: streamId,
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
          [streamId]: previousTags,
        }));
        setSnackbarMessage(
          'Ошибка при обновлении тегов, попробуйте снова'
        );
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
      }
    },
    [selectedTags]
  );

  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

  const handleViewChange = (event, newView) => {
    if (newView !== null) {
      setView(newView);
    }
  };

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
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        pt: { xs: '105px', md: '0' }, // Отступ сверху на маленьких экранах
      }}
    >
      <MenuBox>
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
          <ToggleButtonGroup
            value={view}
            exclusive
            onChange={handleViewChange}
            aria-label="view"
          >
            <ToggleButton value="allStreams" aria-label="all streams">
              Все наборы
            </ToggleButton>
            <ToggleButton value="userStreams" aria-label="user streams">
              Твои наборы
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </MenuBox>

      <ScrollContainer>
        {view === 'userStreams' ? (
          <ContainerBox>
            <List>
              {streams
                .filter((stream) => !globalExclude.includes(stream.streamId))
                .map((stream) => (
                  <StreamItem key={stream.streamId} checked={userStreams.includes(stream.streamId)}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                      <FormControlLabel
                        control={
                          <IconButton
                            onClick={() => handleUserCheckboxChange(stream.streamId)}
                            aria-label="toggle stream visibility"
                          >
                            <img
                              src={userStreams.includes(stream.streamId) ? showIcon : hideIcon}
                              alt={userStreams.includes(stream.streamId) ? 'Show Stream' : 'Hide Stream'}
                              style={{ width: 24, height: 24 }}
                            />
                          </IconButton>
                        }
                        label={stream.name}
                      />
                      <Autocomplete
                        multiple
                        id={`tags-outlined-${stream.streamId}`}
                        options={tags}
                        getOptionLabel={(option) => option}
                        filterSelectedOptions
                        value={selectedTags[stream.streamId] || []}
                        onChange={(event, newValue) => handleTagChange(event, newValue, stream.streamId)}
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
                  </StreamItem>
                ))}
            </List>
          </ContainerBox>
        ) : (
          <ContainerBox>
            <List>
              {streams.map((stream) => (
                <StreamItem key={stream.streamId} checked={!globalExclude.includes(stream.streamId)}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                    <FormControlLabel
                      control={
                        <IconButton
                          onClick={() => handleCheckboxChange(stream.streamId)}
                          aria-label="toggle stream visibility"
                        >
                          <img
                            src={!globalExclude.includes(stream.streamId) ? showIcon : hideIcon}
                            alt={!globalExclude.includes(stream.streamId) ? 'Show Stream' : 'Hide Stream'}
                            style={{ width: 24, height: 24 }}
                          />
                        </IconButton>
                      }
                      label={stream.name}
                    />
                    <Autocomplete
                      multiple
                      id={`tags-outlined-${stream.streamId}`}
                      options={tags}
                      getOptionLabel={(option) => option}
                      filterSelectedOptions
                      value={selectedTags[stream.streamId] || []}
                      onChange={(event, newValue) => handleTagChange(event, newValue, stream.streamId)}
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
                </StreamItem>
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