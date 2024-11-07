import React from 'react';
import { Navigate } from 'react-router-dom';
import axios from 'axios';
import axiosInstance from "./axiosInstance";

const PrivateRoute = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = React.useState(null);

  React.useEffect(() => {
    const checkAuth = async () => {
      try {
        await axiosInstance.get('/protected-route', { withCredentials: true });
        setIsAuthenticated(true);
      } catch (error) {
        setIsAuthenticated(false);
      }
    };

    checkAuth();
  }, []);

  if (isAuthenticated === null) {
    return <div>Loading...</div>; // Или любой индикатор загрузки
  }

  return isAuthenticated ? children : <Navigate to="/signin" />;
};

export default PrivateRoute;
