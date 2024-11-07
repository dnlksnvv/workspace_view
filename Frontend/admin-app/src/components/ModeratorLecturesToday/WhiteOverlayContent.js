import React, { useState, useRef, useEffect } from 'react';
import {
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  Tooltip,
  Snackbar,
  Slider,
  Box,
  TextField,
  MenuItem,
  Select,
  InputLabel,
  FormControl,
  IconButton, Autocomplete,
} from '@mui/material';
import ReactPlayer from 'react-player';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import {
  OverlayContainer,
  WhiteBlock,
  TopSection,
  VideoContainer,
  VideoBox,
  VideoListBox,
  BottomSection,
  LoadingPlaceholder,
  ProcessingText,
  NoRecordsContainer,
  NoRecordsIcon,
  ScrollableCardContainer,
  RefreshCard,
  TrimContainer,
} from './WhiteOverlayStyles';
import axiosInstance, { axiosGoService } from '../axiosInstance';

const formatFileSize = (size) => {
  if (size >= 1073741824) {
    return (size / 1073741824).toFixed(2) + ' GB';
  } else if (size >= 1048576) {
    return (size / 1048576).toFixed(2) + ' MB';
  } else if (size >= 1024) {
    return (size / 1024).toFixed(2) + ' KB';
  } else {
    return size + ' bytes';
  }
};

const formatTime = (time) => {
  return new Date(time).toLocaleString('ru-RU', { timeZone: 'Europe/Moscow', hour: '2-digit', minute: '2-digit' });
};


const formatTimeDisplay = (seconds) => {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hrs > 0) {
    return `${hrs}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  } else if (mins > 0) {
    return `${mins}:${String(secs).padStart(2, '0')}`;
  } else {
    return `0:${String(secs).padStart(2, '0')}`;
  }
};


const WhiteOverlayContent = ({ onClose, videoList, onRefresh, loading, noMeetingsMessage }) => {
  const [folders, setFolders] = useState([]);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [videoSrc, setVideoSrc] = useState('');
  const [currentRecording, setCurrentRecording] = useState(null);
  const [startTime, setStartTime] = useState(0);
  const [endTime, setEndTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [selectedOption, setSelectedOption] = useState('');
  const [downloadLink, setDownloadLink] = useState('');
  const [isLinkMode, setIsLinkMode] = useState(true);
  const [filteredOptions, setFilteredOptions] = useState([]);
  const [searchText, setSearchText] = useState('');
  const [isDownloadStarted, setIsDownloadStarted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const playerRef = useRef(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFolderName, setSelectedFolderName] = useState('');
  const [selectedFolderId, setSelectedFolderId] = useState('');


const [isFetching, setIsFetching] = useState(false);

useEffect(() => {
  // Если нет обработки, есть текущая запись и запрос еще не в процессе, то выполняем его
  if (!processing && currentRecording && !isFetching) {
    setIsFetching(true); // Флаг, указывающий, что запрос начат
    setIsLoading(true); // Показываем индикатор загрузки

    const isTrimmed = currentRecording.trim === true;
    fetchVideoRecording(
      currentRecording.recording_id,
      videoList.closest_conference_uuid,
      setSnackbarMessage,
      setVideoSrc,
      isTrimmed
    ).finally(() => {
      setIsLoading(false); // Скрываем индикатор загрузки
      setIsFetching(false); // Сбрасываем флаг после завершения запроса
    });
  }
}, [processing, currentRecording, videoList]);

const [abortController, setAbortController] = useState(null);

const fetchVideoRecording = async (recordingId, uuid, setSnackbarMessage, setVideoSrc, isTrimmed) => {
  // Если запрос уже выполняется, возвращаемся
  if (isFetching) {
    console.log('Запрос уже выполняется. Пропуск.');
    return;
  }

  // Создаем новый AbortController для управления запросом
  const controller = new AbortController();
  setAbortController(controller);

  setIsFetching(true);
  setIsLoading(true);

  try {
    const trimmedRecordingId = isTrimmed ? `${recordingId}_trimmed` : recordingId;
    const response = await axiosInstance.get('/get-recording', {
      params: {
        recording_id: trimmedRecordingId,
        conference_uuid: uuid,
      },
      responseType: 'blob',
      headers: {
        Range: 'bytes=0-', // Запрашиваем с поддержкой частичной загрузки
      },
      signal: controller.signal, // Передаем сигнал AbortController
    });

    const videoBlob = response.data;
    const videoUrl = URL.createObjectURL(videoBlob);
    setVideoSrc(videoUrl);

    console.log(`Successfully fetched recording ID: ${trimmedRecordingId}`, response.data);
  } catch (error) {
    if (error.name === 'CanceledError') {
      console.log('Запрос был отменен');
    } else {
      console.error('Error fetching recording ID:', error);
      setSnackbarMessage('Ошибка при запросе видео. Попробуйте снова.');
    }
  } finally {
    setIsLoading(false);
    setIsFetching(false);
  }
};
const checkProcessingStatus = (recording) => {
  return recording.trimming_in_progress === true;
};
const checkVideoStatus = async (recordingId, conferenceUuid) => {
  try {
    const response = await axiosGoService.post('/check-video-status', {
      recording_id: recordingId,
      conference_uuid: conferenceUuid,
    });

    // Проверяем ответ от сервера
    if (response.data && response.data.kinescope_status === 'done') {
      console.log('Видео найдено:', response.data);

      // Обновляем downloadLink значением kinescope_code из ответа
      if (response.data.kinescope_code) {
        setDownloadLink(`https://kinescope.io/${response.data.kinescope_code}`);
      }

      setSnackbarMessage('Видео успешно найдено!');
      setSnackbarOpen(true);

      // Обновляем видео список после успешной проверки статуса
      onRefresh();
    } else {
      console.log('Видео не найдено или нет данных.');
      setSnackbarMessage('Видео не найдено. Повторите попытку позже.');
      setSnackbarOpen(true);
    }
  } catch (error) {
    console.error('Ошибка при проверке статуса видео:', error);
    setSnackbarMessage('Ошибка при проверке статуса видео. Попробуйте снова.');
    setSnackbarOpen(true);
  }
};

const requestVideoUploadToKinescope = async (folder, recordingId, conferenceUuid) => {
  try {
    console.log('Отправка запроса на сервер Go', folder, recordingId, conferenceUuid);

    const response = await axiosGoService.post('/receive-folder-info', {
      folder_id: folder.id,
      project_id: folder.project_id,
      parent_id: folder.parent_id,
      recording_id: recordingId,
      conference_uuid: conferenceUuid,
    }, {
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
      }
    });

    console.log('Информация о папке и видео успешно отправлена на сервер:', response.data);
    setSnackbarMessage('Видео успешно загружено на сервер!');
    setSnackbarOpen(true);
    setUploadProgress(100);

    // Добавьте вызов функции для проверки статуса
    checkVideoStatus(recordingId, conferenceUuid);

  } catch (error) {
    console.error('Ошибка при отправке информации о папке и видео на сервер:', error);
    setSnackbarMessage('Ошибка загрузки видео. Попробуйте снова.');
    setSnackbarOpen(true);
  }
};



  useEffect(() => {
    setStartTime(0);
    setEndTime(duration);
  }, [duration]);

  useEffect(() => {
  const fetchFolders = async () => {
    try {
      const response = await axiosInstance.get('/kinescope-folders');

      // Проверяем структуру данных, получаемых из ответа
      console.log('Ответ от /kinescope-folders:', response.data);

      // Преобразуем данные в нужный формат
      const folderData = Object.entries(response.data.couples).map(([key, value]) => ({
        id: key,
        name: value.name,
        project_id: value.project_id,
        parent_id: value.parent_id,
      }));

      console.log('Сформированный массив папок:', folderData);

      setFolders(folderData);
    } catch (error) {
      console.error('Ошибка при запросе списка папок:', error);
    }
  };

  fetchFolders();
}, []);

  const handleOptionChange = (event, newValue) => {
    setSelectedOption(newValue);
  };


  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

const handleVideoClick = (recording) => {
  setCurrentRecording(recording);
  setIsLoading(true); // Начинаем показ индикатора загрузки

  // Проверка, находится ли видео в процессе обработки
  if (checkProcessingStatus(recording)) {
    setProcessing(true); // Устанавливаем состояние обработки
    setSnackbarMessage('Видео обрабатывается... Пожалуйста, попробуйте позже.');
    setSnackbarOpen(true);
    setIsLoading(false); // Останавливаем показ индикатора загрузки
    return;
  }

  if (recording.download_status === 'not_downloaded') {
    setSnackbarMessage('Видео ещё не загружено на сервер. Пожалуйста, подождите.');
    setSnackbarOpen(true);
    setIsLoading(false); // Останавливаем показ индикатора загрузки
  } else if (recording.download_status === 'downloaded') {
    const isTrimmed = recording.trim === true;
    fetchVideoRecording(recording.recording_id, videoList.closest_conference_uuid, setSnackbarMessage, setVideoSrc, isTrimmed)
      .finally(() => setIsLoading(false)); // Скрываем индикатор загрузки после загрузки видео

    // Проверка наличия kinescope_folder_id
    if (recording.kinescope_folder_id) {
      const folder = folders.find((folder) => folder.id === recording.kinescope_folder_id);
      const folderName = folder ? folder.name : 'Название папки не найдено';
      setSelectedFolderName(folderName);
    } else {
      setSelectedFolderId('');
      setSelectedFolderName('');
    }

    setIsDownloadStarted(recording.kinescope_status === 'done' || recording.kinescope_status === 'uploading');
    setDownloadLink(recording.kinescope_code ? `https://kinescope.io/${recording.kinescope_code}` : '');
  }
};



const handleTrimVideo = () => {
  if (!playerRef.current || !currentRecording) return;

  const recordingId = currentRecording.recording_id;
  const uuid = Object.entries(videoList.meetings).find(([key, meeting]) =>
    meeting.recordings.some((rec) => rec.recording_id === recordingId)
  )?.[0];

  if (!uuid) {
    setSnackbarMessage('Ошибка: UUID не найден для выбранного видео.');
    setSnackbarOpen(true);
    return;
  }

  // Устанавливаем флаг обработки и показываем сообщение
  setProcessing(true);
  setSnackbarMessage('Видео обрабатывается...');
  setSnackbarOpen(true);

  axiosInstance
    .post('/log-trim-info', {
      recording_id: recordingId,
      uuid: uuid,
      start_time: startTime,
      end_time: endTime,
    })
    .then((response) => {
      setSnackbarMessage('Видео успешно обрезано.');
      setSnackbarOpen(true);
      setCurrentRecording((prev) => ({ ...prev, trim: true }));
    })
    .catch((error) => {
      setSnackbarMessage('Ошибка при логировании информации об обрезке.');
      setSnackbarOpen(true);
    })
    .finally(() => {
      // После получения ответа, обновляем список видео и снимаем флаг обработки
      onRefresh();
      setProcessing(false);
    });
};

const handleCancelTrim = () => {
  if (!currentRecording) return;

  const recordingId = currentRecording.recording_id;

  // Отменяем текущий запрос, если он существует
  if (abortController) {
    abortController.abort();
    console.log('Текущий запрос на загрузку видео отменен');
  }

  // Находим правильный UUID для текущей записи
  const uuid = Object.entries(videoList.meetings).find(([key, meeting]) =>
    meeting.recordings.some((rec) => rec.recording_id === recordingId)
  )?.[0];

  if (!uuid) {
    console.error('UUID not found for the selected recording.');
    setSnackbarMessage('Ошибка: UUID не найден для выбранного видео.');
    setSnackbarOpen(true);
    return;
  }

  axiosInstance
    .post('/cancel-trim', {
      recording_id: recordingId,
      uuid: uuid,
    })
    .then((response) => {
      console.log('Trim canceled successfully:', response.data);
      setSnackbarMessage('Обрезка видео отменена.');
      setSnackbarOpen(true);
      setCurrentRecording((prev) => ({ ...prev, trim: false }));

      // Начинаем новую загрузку после отмены обрезки
      fetchVideoRecording(recordingId, uuid, setSnackbarMessage, setVideoSrc, false);
    })
    .catch((error) => {
      console.error('Error canceling trim:', error);
      setSnackbarMessage('Ошибка при отмене обрезки видео.');
      setSnackbarOpen(true);
    });
};

  const handleSliderChange = (event, newValue) => {
    const [newStartTime, newEndTime] = newValue;
    setStartTime(newStartTime);
    setEndTime(newEndTime);

    if (playerRef.current) {
      playerRef.current.seekTo(newStartTime, 'seconds');
    }
  };

  const handleSliderCommit = (event, newValue) => {
    const [newStartTime, newEndTime] = newValue;
    if (playerRef.current) {
      playerRef.current.seekTo(newEndTime, 'seconds');
    }
  };


  const handleCancelUpload = async () => {
  if (!currentRecording) return;

  // Определяем правильный conference_uuid для текущей записи
  const conferenceUuid = Object.entries(videoList.meetings).find(([key, meeting]) =>
    meeting.recordings.some((rec) => rec.recording_id === currentRecording.recording_id)
  )?.[0];

  if (!conferenceUuid) {
    console.error('Не найден UUID конференции для выбранного видео');
    setSnackbarMessage('Ошибка: UUID не найден для выбранного видео.');
    setSnackbarOpen(true);
    return;
  }

  try {
    const response = await axiosGoService.post('/cancel-upload', {
      recording_id: currentRecording.recording_id,
      conference_uuid: conferenceUuid,
    });

    if (response.status === 200) {
      console.log('Запрос на отмену загрузки успешно отправлен:', response.data);
      setSnackbarMessage('Запрос на отмену загрузки успешно обработан.');

      // Сбрасываем флаг загрузки и очищаем ссылку
      setIsDownloadStarted(false);
      setDownloadLink('');
      setUploadProgress(0);

      // Обновляем данные текущей записи
      const updatedRecording = {
        ...currentRecording,
        kinescope_status: null, // Обновляем статус
        kinescope_code: null,   // Очищаем код
      };
      setCurrentRecording(updatedRecording); // Обновляем состояние

      setSnackbarOpen(true);
    } else {
      console.error('Ошибка при отправке запроса на отмену загрузки:', response);
      setSnackbarMessage('Ошибка при отмене загрузки. Попробуйте снова.');
    }
  } catch (error) {
    console.error('Ошибка при отправке запроса на отмену загрузки:', error);
    setSnackbarMessage('Ошибка при отмене загрузки. Попробуйте снова.');
  } finally {
    setSnackbarOpen(true);
  }
};



  const handleCopy = () => {
    navigator.clipboard
      .writeText(downloadLink)
      .then(() => {
        setSnackbarMessage('Скопировано в буфер обмена');
        setSnackbarOpen(true);
      })
      .catch(() => {
        setSnackbarMessage('Не удалось скопировать');
        setSnackbarOpen(true);
      });
  };

  const handleToggleLinkCode = () => {
    setIsLinkMode(!isLinkMode);
  };

  // Обновите функцию handleDownloadClick для отправки данных на сервер при нажатии кнопки
  const handleDownloadClick = () => {
  if (isDownloadStarted) {
    setIsDownloadStarted(false);
    setDownloadLink('');
    setUploadProgress(0); // Сброс прогресса
  } else {
    setIsDownloadStarted(true);

    // Устанавливаем ссылку на скачивание в значение по умолчанию
    if (selectedOption && currentRecording) {
      const recordingId = currentRecording.trim ? `${currentRecording.recording_id}_trimmed` : currentRecording.recording_id;

      // Определяем правильный conference_uuid для текущей записи
      const conferenceUuid = Object.entries(videoList.meetings).find(([key, meeting]) =>
        meeting.recordings.some((rec) => rec.recording_id === currentRecording.recording_id)
      )?.[0];

      if (!conferenceUuid) {
        console.error('Не найден UUID конференции для выбранного видео');
        setSnackbarMessage('Ошибка: UUID не найден для выбранного видео.');
        setSnackbarOpen(true);
        return;
      }

      requestVideoUploadToKinescope(selectedOption, recordingId, conferenceUuid);
    } else {
      console.error('Не выбрана папка или видео');
    }
  }
};

  const sortedMeetings = Object.keys(videoList?.meetings || {}).sort((a, b) => {
    const meetingA = videoList.meetings[a];
    const meetingB = videoList.meetings[b];
    const dateA = meetingA.recordings?.[0]?.start_time ? new Date(meetingA.recordings[0].start_time) : 0;
    const dateB = meetingB.recordings?.[0]?.start_time ? new Date(meetingB.recordings[0].start_time) : 0;
    return dateB - dateA;
  });

  const isTrimButtonDisabled = startTime === endTime;

  return (
  <OverlayContainer>
    <WhiteBlock>
      <TopSection>
        <VideoContainer>
          <VideoBox>
  {isLoading ? (
    <LoadingPlaceholder>
      <Typography variant="h6" align="center">Загрузка...</Typography>
    </LoadingPlaceholder>
  ) : (
    videoSrc ? (
      <ReactPlayer
        ref={playerRef}
        url={videoSrc}
        controls
        width="100%"
        height="100%"
        onDuration={(duration) => setDuration(duration)}
        onProgress={({ playedSeconds }) => {
          if (playedSeconds < startTime || playedSeconds > endTime) {
            playerRef.current.seekTo(startTime, 'seconds');
          }
        }}
      />
    ) : (
      <Typography
        variant="h6"
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          color: 'textSecondary',
          fontSize: {
            xs: '0.875rem',
            sm: '1rem',
          },
        }}
      >
        Video Placeholder
      </Typography>
    )
  )}
</VideoBox>

          {videoSrc && !processing && (
            <TrimContainer>
              {/* Инструменты обрезки и кнопка отмены обрезки */}
              {!currentRecording?.trim && !isDownloadStarted && (
                <>
                  <Slider
                    value={[startTime, endTime]}
                    onChange={handleSliderChange}
                    onChangeCommitted={handleSliderCommit}
                    min={0}
                    max={duration}
                    valueLabelDisplay="auto"
                    aria-labelledby="range-slider"
                    sx={{ width: '100%' }}
                  />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', mt: 1 }}>
                    <Typography variant="body2" sx={{ padding: '4px 8px', backgroundColor: '#f0f0f0', borderRadius: '8px' }}>
  {formatTimeDisplay(startTime)}
</Typography>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={handleTrimVideo}
                      disabled={isTrimButtonDisabled}
                      sx={{ minWidth: '120px' }}
                    >
                      Обрезать видео
                    </Button>
                    <Typography variant="body2" sx={{ padding: '4px 8px', backgroundColor: '#f0f0f0', borderRadius: '8px' }}>
  {formatTimeDisplay(endTime)}
</Typography>
                  </Box>
                </>
              )}

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, width: '100%', mt: 2 }}>
                {/* Кнопка отмены обрезки, если видео обрезано и не начата загрузка */}
                {currentRecording?.trim && !isDownloadStarted && (
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={handleCancelTrim}
                    sx={{ width: '100%' }}
                  >
                    Отменить обрезку
                  </Button>
                )}

                {/* Кнопка отмены загрузки, если загрузка начата */}
                {isDownloadStarted && (
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={handleCancelUpload}
                    sx={{ width: '100%', mb: 1 }}
                  >
                    Отменить загрузку
                  </Button>
                )}

                {/* Отображение выбранной папки или поле для выбора папки */}
                {selectedFolderName ? (
                  <FormControl fullWidth>
                    <TextField
                      variant="outlined"
                      size="small"
                      label="Название папки"
                      value={selectedFolderName || ''}
                      disabled={Boolean(selectedFolderId)} // Если есть ID папки, делаем поле недоступным для редактирования
                      InputProps={{
                        readOnly: Boolean(selectedFolderId), // Устанавливаем только для чтения
                      }}
                      sx={{ mt: 2 }}
                    />
                  </FormControl>
                ) : (
                  <FormControl fullWidth>
                    <Autocomplete
                      options={folders}
                      getOptionLabel={(option) => option.name}
                      value={selectedOption}
                      onChange={handleOptionChange}
                      inputValue={searchText}
                      onInputChange={(event, newInputValue) => setSearchText(newInputValue)}
                      renderInput={(params) => (
                        <TextField {...params} label="Выберите папку kinescope" variant="outlined" size="small" />
                      )}
                    />
                  </FormControl>
                )}

                {!isDownloadStarted && (
                  <Box sx={{ width: '100%', mt: 2 }}>
                    {/* Кнопка для начала загрузки */}
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={handleDownloadClick}
                      disabled={!currentRecording?.trim}
                      sx={{ width: '100%' }}
                    >
                      Начать загрузку
                    </Button>
                  </Box>
                )}

                {/* Прогресс загрузки */}
                {isDownloadStarted && !downloadLink && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption">Прогресс загрузки: {uploadProgress}%</Typography>
                    <Box sx={{ width: '100%', backgroundColor: '#e0e0e0', height: 10, mt: 1 }}>
                      <Box
                        sx={{
                          width: `${uploadProgress}%`,
                          backgroundColor: uploadProgress === 100 ? 'green' : '#3f51b5',
                          height: '100%',
                          transition: 'width 0.2s ease-in-out',
                        }}
                      />
                    </Box>
                  </Box>
                )}

                {/* Ссылка на загруженное видео */}
                {downloadLink && (
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', mt: 2 }}>
                    <IconButton onClick={handleToggleLinkCode} sx={{ marginRight: 1 }}>
                      <SwapHorizIcon />
                    </IconButton>
                    <TextField value={downloadLink} fullWidth variant="outlined" size="small" InputProps={{ readOnly: true }} />
                    <IconButton onClick={handleCopy}>
                      <ContentCopyIcon />
                    </IconButton>
                  </Box>
                )}
              </Box>
            </TrimContainer>
          )}

          {processing && (
  <Box sx={{ textAlign: 'center', mt: 2 }}>
    <Typography variant="body1" color="error">Видео обрабатывается... Пожалуйста, попробуйте позже.</Typography>
    <Button variant="outlined" color="error" onClick={handleCancelTrim} sx={{ mt: 2 }}>
      Отменить обрезку
    </Button>
  </Box>
)}
        </VideoContainer>
        <VideoListBox>
          <ScrollableCardContainer>
            <List>
              <RefreshCard onClick={onRefresh}>
                <Typography variant="button">{loading ? 'Загрузка...' : 'Обновить'}</Typography>
              </RefreshCard>

              {loading ? (
                Array.from({ length: 3 }).map((_, index) => <LoadingPlaceholder key={index} />)
              ) : noMeetingsMessage ? (
                <NoRecordsContainer>
                  <NoRecordsIcon />
                  <Typography variant="h6" align="center">
                    {noMeetingsMessage}
                  </Typography>
                </NoRecordsContainer>
              ) : sortedMeetings.length === 0 ? (
                <NoRecordsContainer>
                  <NoRecordsIcon />
                  <Typography variant="h6" align="center">
                    Упс, ничего нет.
                  </Typography>
                  <Typography variant="h6" align="center">
                    Дождись окончания конференции.
                  </Typography>
                </NoRecordsContainer>
              ) : (
                sortedMeetings.map((uuid) => {
                  const meeting = videoList.meetings[uuid];
                  const isClosest = uuid === videoList.closest_conference_uuid;
                  const status = meeting.status;

                  if (status === 'processing') {
                    return (
                      <Tooltip title="Файл обрабатывается..." arrow key={uuid}>
                        <ListItem
                          sx={{
                            backgroundColor: '#e0e0e0',
                            color: '#999',
                            cursor: 'not-allowed',
                            marginBottom: '10px',
                            borderRadius: '8px',
                            textAlign: 'center',
                          }}
                        >
                          <ProcessingText>
                            Видео обрабатывается
                            <span>.</span>
                            <span>.</span>
                            <span>.</span>
                          </ProcessingText>
                        </ListItem>
                      </Tooltip>
                    );
                  }

                  const startTime = formatTime(meeting.recordings[0].start_time);
                  const endTime = formatTime(meeting.recordings[0].end_time);
                  const fileSize = formatFileSize(meeting.recordings[0].file_size);

                  const sharedScreenRecording = meeting.recordings.find(
                    (rec) => rec.recording_type === 'shared_screen_with_speaker_view'
                  );

                  let downloadMessage = '';
                  if (sharedScreenRecording) {
                    downloadMessage =
                      sharedScreenRecording.download_status === 'downloaded'
                        ? 'Видео готово к редактированию'
                        : 'Видео не загружено на сервер';
                  }

                  return (
                    <Tooltip title={isClosest ? 'Вероятно, это ваша лекция' : ''} arrow key={uuid}>
                      <ListItem
                        button
                        onClick={() => handleVideoClick(sharedScreenRecording)}
                        sx={{
                          backgroundColor: isClosest ? 'rgba(161,230,248,0.77)' : '#e0e0e0',
                          color: '#000',
                          cursor: 'pointer',
                          marginBottom: '10px',
                          borderRadius: '8px',
                          transition: 'transform 0.2s, background-color 0.2s',
                          position: 'relative',
                          zIndex: 1,
                          '&:hover': {
                            transform: 'scale(1.02)',
                            backgroundColor: isClosest ? '#a1e6f8' : '#d0d0d0',
                            zIndex: 2,
                            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)',
                          },
                          overflow: 'hidden',
                          wordWrap: 'break-word',
                          fontSize: {
                            xs: '0.75rem',
                            sm: '1rem',
                          },
                        }}
                      >
                        <ListItemText
                          primary={meeting.topic}
                          secondary={
                            <>
                              <Typography variant="caption" display="block">
                                {`${startTime} - ${endTime}`}
                              </Typography>
                              <Typography variant="caption" display="block">
                                Размер файла: {fileSize}
                              </Typography>
                              {downloadMessage && (
                                <Typography variant="caption" display="block" color="error">
                                  {downloadMessage}
                                </Typography>
                              )}
                            </>
                          }
                        />
                      </ListItem>
                    </Tooltip>
                  );
                })
              )}
            </List>
          </ScrollableCardContainer>
        </VideoListBox>
      </TopSection>
      <Button onClick={onClose} sx={{ marginTop: 'auto' }}>
        Закрыть
      </Button>
    </WhiteBlock>

    {/* Snackbar для уведомлений */}
    <Snackbar
      open={snackbarOpen}
      autoHideDuration={6000}
      onClose={handleSnackbarClose}
      message={snackbarMessage}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
    />
  </OverlayContainer>
);
};

export default WhiteOverlayContent;
