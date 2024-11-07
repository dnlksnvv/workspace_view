import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../axiosInstance';
import {
  Typography, Container, Box, Card, CardContent, CardHeader, Drawer,
  IconButton, Menu, MenuItem, FormGroup, FormControlLabel, Checkbox, FormControl, InputLabel, Select,
} from '@mui/material';
import { Book, Info, AccessTime, Person, Description, Duo, FileCopy, MoreVert, CalendarToday } from '@mui/icons-material';
import { styled } from '@mui/system';
import { MessageBox } from 'react-chat-elements';
import 'react-chat-elements/dist/main.css';
import { CopyToClipboard } from 'react-copy-to-clipboard';
import ZoomLogoGray from './Zoom - Blue.svg';

const StyledCard = styled(Card)(({ theme }) => ({
  marginTop: theme.spacing(2),
  width: '100%',
  borderRadius: '15px',
  backgroundColor: '#e3f2fd',
  boxShadow: '0 3px 5px rgba(0,0,0,0.3)',
  transition: 'transform 0.3s ease, box-shadow 0.3s ease',
  '&:hover': {
    transform: 'scale(1.05)',
    boxShadow: '0 6px 10px rgba(0,0,0,0.4)',
  },
  position: 'relative',
}));

const CustomDrawer = styled(Drawer)(({ theme }) => ({
  '& .MuiDrawer-paper': {
    width: '600px',
    padding: theme.spacing(2),
    boxShadow: '0 3px 5px rgba(0,0,0,0.3)',
  },
}));

const ZoomIcon = styled('img')(({ theme, isColored }) => ({
  position: 'absolute',
  top: theme.spacing(1),
  right: theme.spacing(7),
  width: '100px',
  height: 'auto',
  filter: isColored ? 'none' : 'grayscale(100%)',
  transition: 'filter 0.3s ease',
}));

const CustomMessageBox = styled(Box)(({ theme }) => ({
  position: 'relative',
  whiteSpace: 'pre-line',
  padding: theme.spacing(2),
}));

const CopyButton = styled(IconButton)(({ theme }) => ({
  position: 'absolute',
  bottom: theme.spacing(3),
  right: theme.spacing(5),
}));

const FiltersContainer = styled(Box)(({ theme }) => ({
  position: 'fixed',
  top: theme.spacing(8),
  left: 0,
  width: '250px',
  height: 'calc(100vh - 64px)',
  overflowY: 'auto',
  padding: theme.spacing(2),
  boxShadow: '2px 0 5px rgba(0,0,0,0.1)',
  backgroundColor: '#f4f4f4',
}));

const LecturesContainer = styled(Box)(({ theme }) => ({
  marginLeft: '270px',
  flexGrow: 1,
}));

export default function ModeratorLecturesArchive() {
  const navigate = useNavigate();
  const email = '1';
  const [lectures, setLectures] = useState([]);
  const [selectedLecture, setSelectedLecture] = useState(null);
  const [noteContent, setNoteContent] = useState({
    upperText: '',
    lowerText: ''
  });
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedSheetNames, setSelectedSheetNames] = useState([]);
  const [sortOrder, setSortOrder] = useState('desc');
  const [uniqueSheetNames, setUniqueSheetNames] = useState([]);

  const fetchConferenceData = async (conferenceId) => {
    try {
      const response = await axiosInstance.get('/zoom_service/get_conference_data', {
        params: { conference_id: conferenceId },
      });
      if (response.data.meeting_details) {
        return response.data;
      }
    } catch (error) {
      console.error(`Ошибка при получении данных конференции для ID ${conferenceId}:`, error);
    }
    return null;
  };

  const fetchLectures = async () => {
    try {
      const response = await axiosInstance.get('/schedule_service/archive_lectures', {
        params: { email },
      });
      const lecturesWithConferenceData = await Promise.all(
        response.data.map(async (lecture) => {
          const conferenceData = await fetchConferenceData(lecture.id);
          return { ...lecture, conferenceData };
        })
      );
      setLectures(lecturesWithConferenceData);
      setUniqueSheetNames([...new Set(lecturesWithConferenceData.map(lecture => lecture.sheet_name))]);
    } catch (error) {
      console.error('Ошибка при получении данных:', error);
    }
  };

  useEffect(() => {
    if (email) {
      fetchLectures();
    } else {
      navigate('/signin');
    }
  }, [email, navigate]);

  const handleCardClick = async (lecture) => {
    setSelectedLecture(lecture);
    if (lecture.conferenceData) {
      updateNoteContent(lecture.conferenceData);
    } else {
      const conferenceData = await fetchConferenceData(lecture.id);
      if (conferenceData) {
        updateNoteContent(conferenceData);
      } else {
        setNoteContent({ upperText: '', lowerText: '' });
      }
    }
  };

  const handleDrawerClose = () => {
    setSelectedLecture(null);
  };

  const updateNoteContent = (responseData) => {
    if (!responseData || !responseData.meeting_details || !responseData.meeting_details.length) {
      setNoteContent({ upperText: '', lowerText: '' });
      return;
    }

    const meetingDetails = responseData.meeting_details[0];
    const upperText = `
Тема: ${meetingDetails.topic}
Дата: ${meetingDetails.date}
`;

    const lowerText = `
Коллеги, добрый день!
Напоминаем о сегодняшнем вебинаре

Спикер: ${meetingDetails.speaker}
📌 Время: ${meetingDetails.time_meeting}
📌 Тема: ${meetingDetails.theme}
📌 Ссылка для подключения: ${meetingDetails.link}

Идентификатор конференции: ${meetingDetails.id}
Код доступа: ${meetingDetails.code}

Хорошего дня!
`;

    setNoteContent({
      upperText: upperText.trim(),
      lowerText: lowerText.trim(),
    });
  };

  const handleCheckboxChange = (event) => {
    const value = event.target.value;
    setSelectedSheetNames((prev) =>
      prev.includes(value) ? prev.filter((name) => name !== value) : [...prev, value]
    );
  };

  const handleSortChange = (event) => {
    setSortOrder(event.target.value);
  };

  const parseDate = (dateString) => {
    const parts = dateString.split('.');
    return new Date(parts[2], parts[1] - 1, parts[0]);
  };

  const filteredLectures = lectures
    .filter((lecture) => selectedSheetNames.length === 0 || selectedSheetNames.includes(lecture.sheet_name))
    .sort((a, b) => {
      const dateA = parseDate(a.date.split(', ')[1]);
      const dateB = parseDate(b.date.split(', ')[1]);
      return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
    });

  return (
    <Container component="main" maxWidth="lg">
      <Box sx={{ display: 'flex', width: '100%' }}>
        <FiltersContainer>
          <Typography variant="h6">Фильтры</Typography>
          <FormControl fullWidth sx={{ marginTop: 2 }}>
            <InputLabel>Сортировка по дате</InputLabel>
            <Select value={sortOrder} onChange={handleSortChange}>
              <MenuItem value="asc">От старых к новым</MenuItem>
              <MenuItem value="desc">От новых к старым</MenuItem>
            </Select>
          </FormControl>
          <FormGroup sx={{ marginTop: 2 }}>
            {uniqueSheetNames.map((name) => (
              <FormControlLabel
                control={
                  <Checkbox
                    checked={selectedSheetNames.includes(name)}
                    onChange={handleCheckboxChange}
                    value={name}
                  />
                }
                label={name}
                key={name}
              />
            ))}
          </FormGroup>
        </FiltersContainer>
        <LecturesContainer>
          <Box
            sx={{
              marginTop: 8,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
            }}
          >
            <Typography component="h1" variant="h5" gutterBottom>
              Архив лекций
            </Typography>
            {filteredLectures.length > 0 ? (
              filteredLectures.map((lecture, index) => (
                <StyledCard key={index} onClick={() => handleCardClick(lecture)}>
                  <CardHeader
                    title={lecture.sheet_name}
                    titleTypographyProps={{ variant: 'h6' }}
                  />
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={1}>
                      <Book sx={{ mr: 1 }} />
                      <Typography variant="body1">
                        <strong>Поток:</strong> {lecture.stream}
                      </Typography>
                    </Box>
                    <Box display="flex" alignItems="center" mb={1}>
                      <Info sx={{ mr: 1 }} />
                      <Typography variant="body1">
                        <strong>Тема:</strong> {lecture.topic}
                      </Typography>
                    </Box>
                    <Box display="flex" alignItems="center" mb={1}>
                      <CalendarToday sx={{ mr: 1 }} />
                      <Typography variant="body1">
                        <strong>Дата:</strong> {lecture.date}
                      </Typography>
                    </Box>
                    <Box display="flex" alignItems="center" mb={1}>
                      <AccessTime sx={{ mr: 1 }} />
                      <Typography variant="body1">
                        <strong>Время:</strong> {lecture.time}
                      </Typography>
                    </Box>
                    <Box display="flex" alignItems="center" mb={1}>
                      <Person sx={{ mr: 1 }} />
                      <Typography variant="body1">
                        <strong>Спикер:</strong> {lecture.speaker}
                      </Typography>
                    </Box>
                    {lecture.description && (
                      <Box display="flex" alignItems="center" mb={1}>
                        <Description sx={{ mr: 1 }} />
                        <Typography variant="body1">
                          <strong>Описание:</strong> {lecture.description}
                        </Typography>
                      </Box>
                    )}
                    <Box display="flex" alignItems="center" mb={1}>
                      <Duo sx={{ mr: 1 }} />
                      <Typography variant="body1">
                        <strong>Zoom:</strong> {lecture.zoom}
                      </Typography>
                    </Box>
                  </CardContent>
                  <ZoomIcon src={ZoomLogoGray} isColored={Boolean(lecture.conferenceData)} />
                </StyledCard>
              ))
            ) : (
              <Typography>Нет прошедших лекций.</Typography>
            )}
          </Box>
        </LecturesContainer>
      </Box>
      <CustomDrawer
        anchor="right"
        open={Boolean(selectedLecture)}
        onClose={handleDrawerClose}
      >
        {selectedLecture && (
          <Box>
            <Typography variant="h6">Детали лекции</Typography>
            <Box mt={2}>
              <Box
                sx={{
                  border: '1px solid #1976d2',
                  borderRadius: '4px',
                  padding: '8px',
                  marginBottom: '16px',
                  cursor: 'pointer',
                }}
              >
                <Typography variant="body1"><strong>Поток:</strong> {selectedLecture.stream}</Typography>
              </Box>
              <Box
                sx={{
                  border: '1px solid #1976d2',
                  borderRadius: '4px',
                  padding: '8px',
                  marginBottom: '16px',
                  cursor: 'pointer',
                }}
              >
                <Typography variant="body1"><strong>Тема:</strong> {selectedLecture.topic}</Typography>
              </Box>
              <Box
                sx={{
                  border: '1px solid #1976d2',
                  borderRadius: '4px',
                  padding: '8px',
                  marginBottom: '16px',
                  cursor: 'pointer',
                }}
              >
                <Typography variant="body1"><strong>Дата:</strong> {selectedLecture.date}</Typography>
              </Box>
              <Box
                sx={{
                  border: '1px солид #1976d2',
                  borderRadius: '4px',
                  padding: '8px',
                  marginBottom: '16px',
                  cursor: 'pointer',
                }}
              >
                <Typography variant="body1"><strong>Время:</strong> {selectedLecture.time}</Typography>
              </Box>
              <Box
                sx={{
                  border: '1px solid #1976d2',
                  borderRadius: '4px',
                  padding: '8px',
                  marginBottom: '16px',
                  cursor: 'pointer',
                }}
              >
                <Typography variant="body1"><strong>Спикер:</strong> {selectedLecture.speaker}</Typography>
              </Box>
              <Box
                sx={{
                  border: '1px solid #1976d2',
                  borderRadius: '4px',
                  padding: '8px',
                  marginBottom: '16px',
                  cursor: 'pointer',
                }}
              >
                <Typography variant="body1"><strong>Описание:</strong> {selectedLecture.description}</Typography>
              </Box>
              <Box
                sx={{
                  border: '1px solid #1976d2',
                  borderRadius: '4px',
                  padding: '8px',
                  marginBottom: '16px',
                  cursor: 'pointer',
                }}
              >
                <Typography variant="body1"><strong>Zoom:</strong> {selectedLecture.zoom}</Typography>
              </Box>
              <Typography variant="body1"><strong>Расписание:</strong> <a href={selectedLecture.link} target="_blank" rel="noopener noreferrer">Открыть в Google Sheets</a></Typography>
              <Typography variant="body1"><strong>Номер строки:</strong> {selectedLecture.row_number}</Typography>
              <Typography variant="body1"><strong>ID:</strong> {selectedLecture.id}</Typography>

              <Box
                sx={{
                  borderBottom: '3px solid gray',
                  marginBottom: '16px',
                  marginTop: '16px'
                }}
              />
            </Box>
            {noteContent.upperText && (
              <>
                <Box mt={2} p={2} border="1px solid #1976d2" borderRadius="4px" position="relative">
                  <Typography variant="h6">Сообщение в чат</Typography>
                  <CustomMessageBox>
                    <MessageBox
                      position={'right'}
                      type={'text'}
                      text={noteContent.lowerText} />
                    <CopyToClipboard text={noteContent.lowerText}>
                      <CopyButton>
                        <FileCopy />
                      </CopyButton>
                    </CopyToClipboard>
                  </CustomMessageBox>
                </Box>
              </>
            )}
          </Box>
        )}
      </CustomDrawer>
    </Container>
  );
}
