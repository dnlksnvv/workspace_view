import React, { useEffect, useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemText,
  Divider,
  ListItemIcon,
  IconButton,
  AppBar,
  Toolbar,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import TelegramChannels from './TelegramChannels';
import LMSStreams from './LMSKits';
import Schedules from './Schedule';
import BottomNavBar from '../BottomNavBar/BottomNavBar';

import sheetsIcon from './sheets.png';
import telegramIcon from './telegram.png';
import mdsIcon from './mds.svg';
import accountIcon from './user.png';
import CloseIcon from '@mui/icons-material/Close';
import axiosInstance from '../axiosInstance';
import { useNavigate } from 'react-router-dom';

export default function Settings() {
  const [selectedMenu, setSelectedMenu] = useState(localStorage.getItem('selectedMenu') || 'account');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [user, setUser] = useState({});
  const navigate = useNavigate();

  const handleMenuClick = (menu) => {
    setSelectedMenu(menu);
    localStorage.setItem('selectedMenu', menu);
    setDrawerOpen(false);
  };

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

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar position="fixed" sx={{ display: { xs: 'block', md: 'none' }, backgroundColor: '#2196f3' }}>
        <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <IconButton edge="start" color="inherit" aria-label="menu" onClick={toggleDrawer}>
            <MenuIcon />
          </IconButton>
          <Typography variant="h6">Настройки</Typography>
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

      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={toggleDrawer}
        variant={window.innerWidth >= 768 ? 'permanent' : 'temporary'}
        sx={{
          '& .MuiDrawer-paper': {
            width: { xs: '100%', md: 350 },
            boxSizing: 'border-box',
            position: { xs: 'fixed', md: 'relative' },
            height: '100vh',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          },
        }}
      >
        <List>
          <ListItem
            button
            onClick={() => handleMenuClick('account')}
            sx={{
              backgroundColor: selectedMenu === 'account' ? '#e0e0e0' : 'transparent',
            }}
          >
            <ListItemIcon>
              <img src={accountIcon} alt="Account" style={{ width: 24, height: 24 }} />
            </ListItemIcon>
            <ListItemText primary="Аккаунт" />
          </ListItem>
          <Divider />
          <ListItem
            button
            onClick={() => handleMenuClick('schedules')} // Добавлен новый элемент меню
            sx={{
              backgroundColor: selectedMenu === 'schedules' ? '#e0e0e0' : 'transparent',
            }}
          >
            <ListItemIcon>
              <img src={sheetsIcon} alt="Sheets расписания" style={{ width: 24, height: 24 }} />
            </ListItemIcon>
            <ListItemText primary="Sheets расписания" />
          </ListItem>
          <Divider />
          <ListItem
            button
            onClick={() => handleMenuClick('telegram_channels')}
            sx={{
              backgroundColor: selectedMenu === 'telegram_channels' ? '#e0e0e0' : 'transparent',
            }}
          >
            <ListItemIcon>
              <img src={telegramIcon} alt="Telegram каналы" style={{ width: 24, height: 24 }} />
            </ListItemIcon>
            <ListItemText primary="Telegram каналы" />
          </ListItem>
          <Divider />
          <ListItem
            button
            onClick={() => handleMenuClick('lms_streams')}
            sx={{
              backgroundColor: selectedMenu === 'lms_streams' ? '#e0e0e0' : 'transparent',
            }}
          >
            <ListItemIcon>
              <img src={mdsIcon} alt="LMS наборы" style={{ width: 24, height: 24 }} />
            </ListItemIcon>
            <ListItemText primary="LMS наборы" />
          </ListItem>
        </List>
        <Box sx={{ mt: 'auto', pb: 0 }}>
          <BottomNavBar activePage="/settings" />
        </Box>
      </Drawer>

      {/* Контент выбранного меню */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          justifyContent: 'center',
          flexDirection: 'column',
          alignItems: 'center',
          overflowY: 'hidden',
          height: '100vh',
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
          {selectedMenu === 'account' && (
            <Typography variant="h5">Аккаунт</Typography>
          )}
          {selectedMenu === 'telegram_channels' && <TelegramChannels />}
          {selectedMenu === 'lms_streams' && <LMSStreams />}
          {selectedMenu === 'schedules' && <Schedules />} {/* Новый компонент для отображения расписания */}
        </Container>
      </Box>

      {/* Нижняя навигация для мобильных устройств */}
      <Box sx={{ display: { xs: 'block', md: 'none' }, position: 'fixed', bottom: 0, width: '100%' }}>
        <BottomNavBar activePage="/settings" />
      </Box>
    </Box>
  );
}