import React, { useEffect, useState } from 'react';
import { Modal } from '@mui/material';
import axiosInstance from '../axiosInstance';
import WhiteOverlayContent from './WhiteOverlayContent';

const WhiteOverlay = ({ open, onClose, lectureId }) => {
    const [videoList, setVideoList] = useState([]);
    const [loading, setLoading] = useState(false);

    const fetchData = () => {
        setLoading(true); // Устанавливаем состояние загрузки перед началом запроса
        if (lectureId) {
            axiosInstance.post('/get-conference-video-list', { lectureId })
                .then(response => {
                    console.log('Response:', response.data);
                    setVideoList(response.data);
                })
                .catch(error => {
                    console.error('Error fetching video list:', error);
                })
                .finally(() => setLoading(false)); // Отключаем состояние загрузки после завершения запроса
        }
    };

    useEffect(() => {
        if (open && lectureId) {
            setLoading(true);
            fetchData();
        }
    }, [open, lectureId]);

    return (
        <Modal open={open} onClose={onClose} closeAfterTransition>
            <WhiteOverlayContent onClose={onClose} videoList={videoList} onRefresh={fetchData} loading={loading} />
        </Modal>
    );
};

export default WhiteOverlay;