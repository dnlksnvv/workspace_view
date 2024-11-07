import React from 'react';
import { Box, IconButton } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import homeIcon from './NavBarHome.svg';
import profileIcon from './NavBarUser.svg';
import otherIcon1 from './NavBarToday.svg';
import otherIcon2 from './NavBarNotification.svg';

const BottomNavBar = ({ activePage }) => {
  const navigate = useNavigate();

  const handleNavigate = (path) => {
    if (activePage !== path) {
      navigate(path);
    }
  };

  return (
    <Box
      sx={{
        position: { xs: 'fixed', md: 'relative' },
        bottom: { xs: 0, md: 'auto' },
        width: { xs: '100%', md: '350px' },
        height: '64px',
        backgroundColor: '#f5f5f5',
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
        borderTop: { xs: '1px solid #ddd', md: 'none' },
        zIndex: 1000,
      }}
    >
      <IconButton
        onClick={() => handleNavigate('/home')}
        sx={{
          backgroundColor: activePage === '/home' ? '#e0e0e0' : 'transparent',
          borderRadius: '50%',
          padding: '8px'
        }}
      >
        <img src={homeIcon} alt="Home" style={{ width: 24, height: 24 }} />
      </IconButton>
      <IconButton
        onClick={() => handleNavigate('/moderator/lectures/today')}
        sx={{
          backgroundColor: activePage === '/moderator/lectures/today' ? '#e0e0e0' : 'transparent',
          borderRadius: '50%',
          padding: '8px'
        }}
      >
        <img src={otherIcon1} alt="Other1" style={{ width: 24, height: 24 }} />
      </IconButton>
      <IconButton
        onClick={() => handleNavigate('/')}
        sx={{
          backgroundColor: activePage === '/' ? '#e0e0e0' : 'transparent',
          borderRadius: '50%',
          padding: '8px'
        }}
      >
        <img src={otherIcon2} alt="Other2" style={{ width: 24, height: 24 }} />
      </IconButton>
      <IconButton
        onClick={() => handleNavigate('/settings')}
        sx={{
          backgroundColor: activePage === '/settings' ? '#e0e0e0' : 'transparent',
          borderRadius: '50%',
          padding: '8px'
        }}
      >
        <img src={profileIcon} alt="Profile" style={{ width: 24, height: 24 }} />
      </IconButton>
    </Box>
  );
};

export default BottomNavBar;