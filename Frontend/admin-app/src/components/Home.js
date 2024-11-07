import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Typography,
  Container,
  Box,
  Divider,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  AppBar,
  Toolbar,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import CloseIcon from '@mui/icons-material/Close';
import accountIcon from './Settings/user.png';
import sheetsIcon from './Settings/sheets.png';
import telegramIcon from './Settings/telegram.png';
import mdsIcon from './Settings/mds.svg';
import BottomNavBar from './BottomNavBar/BottomNavBar';
import axiosInstance from './axiosInstance';
import {setThemeColor} from "./utils/setThemeColor";

export default function Home() {
  const navigate = useNavigate();
  const [user, setUser] = useState({});
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await axiosInstance.get('/protected-route', { withCredentials: true });
        setUser(response.data);
      } catch (error) {
        console.error('Not authenticated', error);
        navigate('/signin');
      }
    };

    fetchUserData();
  }, [navigate]);

  useEffect(() => {
    setThemeColor('#2196f3');
  }, []);

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  const handleLogout = () => {
    navigate('/signin');
  };

  const handleGoToTodayLectures = () => {
    navigate('/moderator/lectures/today');
  };

  const handleGoToArchiveLectures = () => {
    navigate('/moderator/lectures/archive');
  };

  const handleGoToSettings = () => {
    navigate('/settings');
  };

  const handleGoToDownloads = () => {
    navigate('/downloads');
  };

  const handleGoToFolders = () => {
    navigate('/folders');
  };

  const handleGoToExternalSite = () => {
    navigate('/external-site');
  };

  const handleGoToStreamsPage = () => {
    navigate('/streams');
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>

      {/* AppBar для маленьких экранов */}
      <AppBar position="fixed" sx={{ display: { xs: 'block', md: 'none' }, backgroundColor: '#2196f3' }}>
        <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <IconButton edge="start" color="inherit" aria-label="menu" onClick={toggleDrawer}>
            <MenuIcon />
          </IconButton>
          <Typography variant="h6">Главная</Typography>
          <IconButton
            edge="end"
            color="inherit"
            aria-label="close"
            onClick={toggleDrawer}
            sx={{ display: drawerOpen ? 'block' : 'none' }}
          >
            <CloseIcon />
          </IconButton>
        </Toolbar>
      </AppBar>


      {/* Drawer для бокового меню */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={toggleDrawer}
        variant={window.innerWidth >= 768 ? 'permanent' : 'temporary'}
        sx={{
          '& .MuiDrawer-paper': {
            width: { xs: '100%', md: 350 },
            boxSizing: 'border-box',
            transition: 'transform 0.3s ease-out',
            position: { xs: 'fixed', md: 'relative' },
            height: { xs: 'auto', md: '100%' },
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          },
        }}
      >
        <List>
          <ListItem button onClick={() => navigate('/account')}>
            <ListItemIcon>
              <img src={accountIcon} alt="Account" style={{ width: 24, height: 24 }} />
            </ListItemIcon>
            <ListItemText primary="Аккаунт" />
          </ListItem>
          <Divider />
          <ListItem button onClick={() => navigate('/lectures')}>
            <ListItemIcon>
              <img src={sheetsIcon} alt="Sheets расписания" style={{ width: 24, height: 24 }} />
            </ListItemIcon>
            <ListItemText primary="Sheets расписания" />
          </ListItem>
          <Divider />
          <ListItem button onClick={() => navigate('/telegram_channels')}>
            <ListItemIcon>
              <img src={telegramIcon} alt="Telegram каналы" style={{ width: 24, height: 24 }} />
            </ListItemIcon>
            <ListItemText primary="Telegram каналы" />
          </ListItem>
          <Divider />
          <ListItem button onClick={() => navigate('/lms_streams')}>
            <ListItemIcon>
              <img src={mdsIcon} alt="LMS наборы" style={{ width: 24, height: 24 }} />
            </ListItemIcon>
            <ListItemText primary="LMS наборы" />
          </ListItem>
        </List>
        {/* Нижнее меню для больших экранов */}
        <Box sx={{ display: { xs: 'none', md: 'block' }, mt: 'auto' }}>
          <BottomNavBar activePage="/home" />
        </Box>
      </Drawer>

      {/* Контент */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          display: 'flex',
          justifyContent: 'center',
        }}
      >
        <Container
          maxWidth="sm"
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            paddingTop: '50px',
          }}
        >
          <Typography component="h1" variant="h5">
            Добро пожаловать, {user.first_name} {user.last_name}
          </Typography>
          <Button onClick={handleGoToTodayLectures} variant="contained" sx={{ mt: 3, mb: 2 }}>
            Лекции на сегодня
          </Button>
          <Button onClick={handleGoToArchiveLectures} variant="contained" sx={{ mt: 3, mb: 2 }}>
            Прошедшие лекции
          </Button>
          <Button onClick={handleGoToDownloads} variant="contained" sx={{ mt: 3, mb: 2 }}>
            Инструмент загрузок
          </Button>
          <Button onClick={handleGoToFolders} variant="contained" sx={{ mt: 3, mb: 2 }}>
            Kinescope файлы
          </Button>
          <Button onClick={handleLogout} variant="contained" sx={{ mt: 3, mb: 2 }}>
            Выйти
          </Button>
        </Container>
      </Box>

      {/* Нижнее меню для маленьких экранов */}
      <Box sx={{ display: { xs: 'block', md: 'none' }, position: 'fixed', bottom: 0, width: '100%' }}>
        <BottomNavBar activePage="/home" />
      </Box>
    </Box>
  );
}
