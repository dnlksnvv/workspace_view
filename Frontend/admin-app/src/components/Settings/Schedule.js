import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  List,
  ListItem,
  FormControlLabel,
  IconButton,
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

const ScheduleItem = React.memo(
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

export default function Schedule() {
  const [loading, setLoading] = useState(true);
  const [globalExclude, setGlobalExclude] = useState([]);
  const [userSchedules, setUserSchedules] = useState([]);
  const [allLists, setAllLists] = useState([]);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('success');
  const [view, setView] = useState('userSchedules');

  useEffect(() => {
    document.body.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = 'auto';
    };
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token'); // Получаем токен из локального хранилища

        const [userScheduleResponse, scheduleResponse] = await Promise.all([
          axiosInstance.post('/schedule/log_user_email', {}, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }),
          axiosInstance.get('/schedule/get_schedules', {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }),
        ]);

        console.log('User Schedule Response:', userScheduleResponse.data);
        console.log('Schedule Response:', scheduleResponse.data);

        setUserSchedules(userScheduleResponse.data.user_schedules);
        setGlobalExclude(scheduleResponse.data.global_exclude);
        setAllLists(scheduleResponse.data.all_lists);

        // Выводим данные для отладки
        console.log('Все названия (allLists):', scheduleResponse.data.all_lists);
        console.log('Названия в globalExclude:', scheduleResponse.data.global_exclude);
        console.log('Названия в "Твои расписания" (userSchedules):', userScheduleResponse.data.user_schedules);

      } catch (error) {
        console.error('Error fetching schedules:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleCheckboxChange = useCallback(
    async (scheduleName) => {
      const isExcluded = globalExclude.includes(scheduleName);
      const action = isExcluded ? 'remove' : 'add';

      setGlobalExclude((prevGlobalExclude) =>
        action === 'add'
          ? [...prevGlobalExclude, scheduleName]
          : prevGlobalExclude.filter((name) => name !== scheduleName)
      );

      try {
        const token = localStorage.getItem('token'); // Получаем токен

        await axiosInstance.post(
          '/schedule_service/update_schedule_exclude',
          {
            schedule_id: scheduleName,
            action: action,
          },
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );
      } catch (error) {
        setGlobalExclude((prevGlobalExclude) =>
          action === 'add'
            ? prevGlobalExclude.filter((name) => name !== scheduleName)
            : [...prevGlobalExclude, scheduleName]
        );
        setSnackbarMessage('Ошибка при обновлении расписания, попробуйте снова');
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
      }
    },
    [globalExclude]
  );

  const handleUserCheckboxChange = useCallback(
    async (scheduleName) => {
      const isUserSchedule = userSchedules.includes(scheduleName);

      setUserSchedules((prevState) =>
        isUserSchedule ? prevState.filter((name) => name !== scheduleName) : [...prevState, scheduleName]
      );

      try {
        const token = localStorage.getItem('token'); // Получаем токен

        await axiosInstance.post(
          '/schedule_service/update_user_schedule',
          {
            schedule_id: scheduleName,
            action: isUserSchedule ? 'remove' : 'add',
          },
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );

        if (!isUserSchedule) {
          setGlobalExclude((prevGlobalExclude) => [...prevGlobalExclude, scheduleName]);
        }
      } catch (error) {
        setUserSchedules((prevState) =>
          isUserSchedule ? [...prevState, scheduleName] : prevState.filter((name) => name !== scheduleName)
        );
        setSnackbarMessage('Ошибка при обновлении статуса расписания, попробуйте снова');
        setSnackbarSeverity('error');
        setSnackbarOpen(true);
      }
    },
    [userSchedules, globalExclude]
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
    return (
      <Box sx={{ height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <img
          src={loadLogo}
          alt="Loading..."
          style={{
            width: '250px',
            height: '250px',
            transform: 'translateY(-25px)',
          }}
        />
      </Box>
    );
  }

  const filteredUserSchedules = allLists.filter(
    (scheduleName) => !globalExclude.includes(scheduleName)
  );

  console.log('Отфильтрованные названия для "Твои расписания":', filteredUserSchedules);

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        pt: { xs: '105px', md: '0' },
      }}
    >
      <MenuBox>
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
          <ToggleButtonGroup value={view} exclusive onChange={handleViewChange} aria-label="view">
            <ToggleButton value="allSchedules" aria-label="all schedules">
              Все расписания
            </ToggleButton>
            <ToggleButton value="userSchedules" aria-label="user schedules">
              Твои расписания
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </MenuBox>

      <ScrollContainer>
        {view === 'userSchedules' ? (
          <ContainerBox>
            <List>
              {filteredUserSchedules.map((scheduleName) => (
                <ScheduleItem
                  key={scheduleName}
                  checked={!userSchedules.includes(scheduleName)}
                >
                  <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                    <FormControlLabel
                                        control={
                        <IconButton
                          onClick={() => handleUserCheckboxChange(scheduleName)}
                          aria-label="toggle schedule visibility"
                        >
                          <img
                            src={!userSchedules.includes(scheduleName) ? showIcon : hideIcon}
                            alt={!userSchedules.includes(scheduleName) ? 'Show Schedule' : 'Hide Schedule'}
                            style={{ width: 24, height: 24 }}
                          />
                        </IconButton>
                      }
                      label={scheduleName}
                    />
                  </Box>
                </ScheduleItem>
              ))}
            </List>
          </ContainerBox>
        ) : (
          <ContainerBox>
            <List>
              {allLists.map((scheduleName) => (
                <ScheduleItem
                  key={scheduleName}
                  checked={!globalExclude.includes(scheduleName)}
                >
                  <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                    <FormControlLabel
                      control={
                        <IconButton
                          onClick={() => handleCheckboxChange(scheduleName)}
                          aria-label="toggle schedule visibility"
                        >
                          <img
                            src={!globalExclude.includes(scheduleName) ? showIcon : hideIcon}
                            alt={!globalExclude.includes(scheduleName) ? 'Show Schedule' : 'Hide Schedule'}
                            style={{ width: 24, height: 24 }}
                          />
                        </IconButton>
                      }
                      label={scheduleName}
                    />
                  </Box>
                </ScheduleItem>
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