import React, {useEffect, useState} from 'react';
import {useNavigate} from 'react-router-dom';
import axiosInstance from '../axiosInstance';
import {Chip, Autocomplete, Input, OutlinedInput, Checkbox, ListItemText, Snackbar} from '@mui/material';
import ClearIcon from '@mui/icons-material/Clear';
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import WhiteOverlay from './WhiteOverlay';
import {
    Typography, Container, Box, Card, CardContent, CardHeader, Drawer, Button, IconButton,
    TextField, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, Menu, Tooltip, Select, MenuItem
} from '@mui/material';
import {
    Schedule,
    Person,
    AccessTime,
    Book,
    Info,
    Description,
    Duo,
    ZoomIn,
    MoreVert,
    FileCopy,
    InfoOutlined,
    Delete,
    Send as SendIcon
} from '@mui/icons-material';
import {styled} from '@mui/system';
import {MessageBox} from 'react-chat-elements';
import 'react-chat-elements/dist/main.css';
import {CopyToClipboard} from 'react-copy-to-clipboard';
import ZoomLogoGray from './Zoom - Blue.svg';
import BottomNavBar from '../BottomNavBar/BottomNavBar';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import MenuIcon from '@mui/icons-material/Menu';
import CloseIcon from '@mui/icons-material/Close';
import accountIcon from '../Settings/user.png';
import sheetsIcon from '../Settings/sheets.png';
import telegramIcon from '../Settings/telegram.png';
import mdsIcon from '../Settings/mds.svg';
import {AppBar, Toolbar, List, ListItem, ListItemIcon, Divider} from '@mui/material';


const PaddedContainer = styled(Container)(({theme}) => ({
    paddingBottom: theme.spacing(12),
    paddingLeft: theme.spacing(0),
    paddingRight: theme.spacing(0),
}));


const TitleBox = styled(Box)(({theme}) => ({
    backgroundColor: '#2196f3',
    borderTopLeftRadius: '0px',
    borderTopRightRadius: '0px',
    borderBottomLeftRadius: '15px',
    borderBottomRightRadius: '15px',
    color: 'white',
    padding: theme.spacing(1),
    paddingRight: theme.spacing(3),
    position: 'relative',
    width: 'calc(100% - 32px)',
    margin: '0 auto',
    textAlign: 'center',
    marginBottom: theme.spacing(-1),
}));


const StyledCard = styled(Card)(({theme}) => ({
    marginTop: theme.spacing(2),
    width: '100%',
    borderRadius: '15px',
    backgroundColor: '#e3f2fd',
    boxShadow: '0 3px 5px rgba(0,0,0,0.3)',
    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
    '&:hover': {
        transform: 'scale(1.03)',
        boxShadow: '0 6px 10px rgba(0,0,0,0.4)',
    },
    position: 'relative',
    [theme.breakpoints.down('sm')]: {
        marginTop: theme.spacing(3),
    },
}));


const NestedCard = styled(Card)(({theme}) => ({
    marginTop: theme.spacing(4),
    width: '98%',
    borderRadius: '15px',
    backgroundColor: '#f1f8e9',
    boxShadow: '0 3px 5px rgba(0,0,0,0.2)',
    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
    '&:hover': {
        transform: 'scale(1.02)',
        boxShadow: '0 6px 10px rgba(0,0,0,0.3)',
    },
    position: 'relative',
    marginLeft: 'auto',
    marginRight: 'auto',
    [theme.breakpoints.down('sm')]: {
        marginTop: theme.spacing(2),
    },
}));

const CustomDrawer = styled(Drawer)(({theme}) => ({
    '& .MuiDrawer-paper': {
        width: '40%',
        padding: theme.spacing(2),
        boxShadow: '0 3px 5px rgba(0,0,0,0.3)',
        [theme.breakpoints.down('md')]: {
            width: '70%', // На средних экранах ширина 60%
        },
        [theme.breakpoints.down('sm')]: {
            width: '92%', // На мобильных устройствах ширина 92%
        },
    },
}));

const ZoomIcon = styled('img')(({theme, isColored}) => ({
    position: 'absolute',
    top: theme.spacing(1),
    right: theme.spacing(1),
    width: '100px',
    height: 'auto',
    filter: isColored ? 'none' : 'grayscale(100%)',
    transition: 'filter 0.3s ease',
}));

const VideoIconButton = styled(IconButton)(({theme, isColored}) => ({
    position: 'absolute',
    top: theme.spacing(8),  // Располагаем кнопку под значком Zoom
    right: theme.spacing(4),
    color: isColored ? 'blue' : 'gray',
    transition: 'color 0.3s ease, transform 0.3s ease',
    '&:hover': {
        transform: isColored ? 'scale(1.2)' : 'scale(1)',
    },
}));

const CenteredButton = styled(Button)(({theme}) => ({
    display: 'block',
    margin: `${theme.spacing(2)} auto`,
    backgroundColor: '#1976d2',
    color: 'white',
    '&:hover': {
        backgroundColor: '#1565c0',
    },
}));

const ErrorTextField = styled(TextField)(({theme, error}) => ({
    '& .MuiOutlinedInput-root': {
        '& fieldset': {
            borderColor: error ? 'red' : 'inherit',
        },
    },
}));

const CustomMessageBox = styled(Box)(({theme}) => ({
    position: 'relative',
    whiteSpace: 'pre-line',
    padding: theme.spacing(2),
    paddingBottom: theme.spacing(6), // Дополнительное пространство для кнопок
}));

const CopyButton = styled(IconButton)(({theme}) => ({
    backgroundColor: 'rgba(211, 211, 211, 0.7)',
    borderRadius: '50%',
    '&:hover': {
        backgroundColor: 'rgba(211, 211, 211, 1)',
    },
}));

const ActionField = styled(Box)(({theme}) => ({
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing(2),
    backgroundColor: 'rgba(211, 211, 211, 0.3)',
    borderRadius: '12px',
    marginTop: theme.spacing(2),
    gap: theme.spacing(1),
    [theme.breakpoints.up('md')]: {
        flexDirection: 'row',
    },
    [theme.breakpoints.between('sm', 'md')]: {
        flexDirection: 'row',
        '& > *': {
            flexBasis: '100%',
            maxWidth: '100%',
        },
    },
    [theme.breakpoints.down('sm')]: {
        flexDirection: 'column',
    },
}));

const ChannelSelectBox = styled(Box)(({theme}) => ({
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing(1),
    width: '100%',
    borderRadius: '4px',
    padding: theme.spacing(0),
    position: 'relative',
    backgroundColor: 'transparent',
    [theme.breakpoints.up('md')]: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    [theme.breakpoints.between('sm', 'md')]: {
        flexDirection: 'row',
        '& .MuiAutocomplete-root': {
            flexBasis: '100%',
            maxWidth: '100%',
        },
    },
}));


const SendButton = styled(IconButton)(({theme}) => ({
    backgroundColor: 'rgba(211, 211, 211, 0.7)',
    borderRadius: '50%',
    '&:hover': {
        backgroundColor: 'rgba(211, 211, 211, 1)',
    },
}));

const DuplicatedLectures = styled(Box)(({theme}) => ({
    marginTop: theme.spacing(2),
    padding: theme.spacing(1),
    border: '1px solid #1976d2',
    borderRadius: '4px',
}));

const DuplicateContainer = styled(Box)(({theme}) => ({
    marginTop: theme.spacing(2),
    padding: theme.spacing(2),
    border: '1px solid #1976d2',
    borderRadius: '4px',
}));


const SelectedChannelChip = styled(Chip)(({theme}) => ({
    margin: theme.spacing(0.5),
    maxWidth: '100%',  // Добавлено для отображения длинных названий
}));


const ChannelAutocomplete = styled(Autocomplete)(({theme}) => ({
    width: '100%',
    '& .MuiInputBase-root': {
        display: 'flex',
        alignItems: 'center',
    },
}));

const ChannelLabel = styled(Typography)(({theme}) => ({
    position: 'absolute',
    top: '-8px',
    left: '12px',
    backgroundColor: 'white',
    padding: '0 4px',
    fontSize: '12px',
    color: 'rgba(0, 0, 0, 0.6)',
}));
export default function ModeratorLecturesToday() {
    const navigate = useNavigate();
    const [lectures, setLectures] = useState([]);
    const [selectedLecture, setSelectedLecture] = useState(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editValues, setEditValues] = useState({
        stream: '',
        topic: '',
        time: '',
        speaker: '',
        description: '',
        zoom: ''
    });
    const [openConfirmDialog, setOpenConfirmDialog] = useState(false);
    const [openRecreateDialog, setOpenRecreateDialog] = useState(false);
    const [recreateConfirm, setRecreateConfirm] = useState('');
    const [noteContent, setNoteContent] = useState({
        upperText: '',
        lowerText: ''
    });
    const [loadingCreate, setLoadingCreate] = useState(false);
    const [loadingRecreate, setLoadingRecreate] = useState(false);
    const [anchorEl, setAnchorEl] = useState(null);
    const [selectedDuplicateLecture, setSelectedDuplicateLecture] = useState('');
    const [duplicateLectures, setDuplicateLectures] = useState([]);
    const [inherited, setInherited] = useState(false);  // Новое состояние для проверки наследования
    const [openModal, setOpenModal] = useState(false);  // Состояние для модального окна
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedChannels, setSelectedChannels] = useState([]);
    const [channels, setChannels] = useState([]);
    const [channelsData, setChannelsData] = useState({});
    const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
    const [deleteConfirm, setDeleteConfirm] = useState('');
    const [loadingDelete, setLoadingDelete] = useState(false);
    const autoDuplicateLectureIds = [];
    const [selectedMenu, setSelectedMenu] = useState('account');
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [snackbarOpen, setSnackbarOpen] = useState(false);
    const [snackbarMessage, setSnackbarMessage] = useState('');


    const handleChannelDelete = async (channelToDelete) => {
        try {
            // Найдите ID канала по имени канала
            const channelId = Object.keys(channelsData).find(id => channelsData[id].name === channelToDelete);

            if (channelId && channelsData[channelId]?.tags) {
                // Выводим теги канала в консоль
                console.log(`Теги для канала ${channelsData[channelId].name}: ${channelsData[channelId].tags.join(', ')}`);

                // Отправляем запрос на удаление тегов
                const response = await axiosInstance.post('/zoom_service/remove_tags', {
                    conference_id: selectedLecture.id.toString(), // Преобразование ID в строку
                    tags: channelsData[channelId].tags
                });

                // Обновляем состояние
                setSelectedChannels((channels) => channels.filter((channel) => channel !== channelToDelete));
                setSelectedLecture(prevLecture => ({
                    ...prevLecture,
                    conferenceData: {
                        ...prevLecture.conferenceData,
                        meeting_details: [{
                            ...prevLecture.conferenceData.meeting_details[0],
                            tags: response.data.tags
                        }]
                    }
                }));
            } else {
                console.error(`Теги для канала ${channelToDelete} не найдены.`);
            }
        } catch (error) {
            console.error('Error removing tags:', error);
        }
    };


    const handleChannelAdd = async (channelToAdd) => {
        try {
            // Найдите ID канала по имени канала
            const channelId = Object.keys(channelsData).find(id => channelsData[id].name === channelToAdd);

            if (channelId && channelsData[channelId]?.tags) {
                // Отправляем запрос на добавление тегов
                const response = await axiosInstance.post('/zoom_service/add_tags', {
                    conference_id: selectedLecture.id.toString(),
                    tags: channelsData[channelId].tags
                });

                // Обновляем состояние
                setSelectedChannels((channels) => [...channels, channelToAdd]);
                setSelectedLecture(prevLecture => ({
                    ...prevLecture,
                    conferenceData: {
                        ...prevLecture.conferenceData,
                        meeting_details: [{
                            ...prevLecture.conferenceData.meeting_details[0],
                            tags: response.data.tags
                        }]
                    }
                }));
            } else {
                console.error(`Теги для канала ${channelToAdd} не найдены.`);
            }
        } catch (error) {
            console.error('Error adding tags:', error);
        }
    };

    const handleChannelChange = (event, newValue) => {
        const addedChannels = newValue.filter(channel => !selectedChannels.includes(channel));
        const deletedChannels = selectedChannels.filter(channel => !newValue.includes(channel));

        if (addedChannels.length > 0) {
            handleChannelAdd(addedChannels[0]);
        } else if (deletedChannels.length > 0) {
            handleChannelDelete(deletedChannels[0]);
        }
    };


    const handleDeleteClick = () => {
    setOpenDeleteDialog(true);
    setAnchorEl(null);
};

const handleDeleteConfirm = async () => {
    const lectureIdDelete = selectedLecture.id.toString();  // Преобразуем ID в строку
    const lectureEmailDelete = selectedLecture.conferenceData.meeting_details[0].email;  // Получаем email
    let meetingIdDelete = selectedLecture.conferenceData.meeting_details[0].id;  // Получаем meeting_id

    // Удаляем все пробелы в meeting_id
    meetingIdDelete = meetingIdDelete.replace(/\s+/g, '');

    if (deleteConfirm === 'УДАЛИТЬ') {
        try {
            setLoadingDelete(true);
            const response = await axiosInstance.post('/zoom_service/delete_conference', {
                conference_id: lectureIdDelete,
                email: lectureEmailDelete,  // Передаем email
                meeting_id: meetingIdDelete  // Передаем meeting_id без пробелов
            });

            console.log("meeting_id:", meetingIdDelete);
            console.log("Response Data:", response.data); // Выводим ответ в консоль

            // Устанавливаем сообщение для Snackbar в зависимости от статуса
            if (response.data.status === "success") {
                setSnackbarMessage("Конференция успешно удалена и в системе, и в Zoom.");
            } else if (response.data.status === "partial_success") {
                setSnackbarMessage("Конференция удалена в системе, но не удалось удалить в Zoom. Пожалуйста, удалите конференцию в Zoom вручную.");
            } else {
                setSnackbarMessage("Произошла ошибка при удалении конференции.");
            }

            setSnackbarOpen(true);

            // После удаления обновляем список лекций
            await fetchLectures();
            handleDrawerClose(); // Закрываем боковое окно
        } catch (error) {
            console.error('Ошибка при удалении конференции:', error);
            setSnackbarMessage('Ошибка при удалении конференции');
            setSnackbarOpen(true);
        } finally {
            setLoadingDelete(false);
        }
        setOpenDeleteDialog(false);
    } else {
        setDeleteConfirm('');
        const dialog = document.getElementById('delete-dialog');
        if (dialog) {
            dialog.style.animation = 'shake 0.5s';
            setTimeout(() => {
                dialog.style.animation = '';
            }, 500);
        }
    }
};







    const handleDeleteDialogClose = () => {
        setOpenDeleteDialog(false);
    };

    const handleDeleteConference = async () => {
        console.log(selectedLecture.id);
        if (selectedLecture) {
            try {
                setLoadingDelete(true);
                const response = await axiosInstance.post('/zoom_service/delete_conference', {
                    conference_id: selectedLecture.id,
                });
                console.log(response.data); // Выводим ответ в консоль

                // После удаления обновляем список лекций
                await fetchLectures();
                handleDrawerClose(); // Закрываем боковое окно
            } catch (error) {
                console.error('Ошибка при удалении конференции:', error);
            } finally {
                setLoadingDelete(false);
            }
        }
    };


    const handleLectureSelect = async (event) => {
        const selectedLectureId = event.target.value;
        if (selectedLectureId) {
            const selectedLectureObj = lectures.find(lecture => lecture.id === selectedLectureId);
            if (selectedLectureObj) {
                console.log('Selected Lecture:', selectedLectureObj); // Вывод информации о лекции в консоль
                setDuplicateLectures(prevLectures => [...prevLectures, selectedLectureObj]);
                setSelectedDuplicateLecture(''); // Сбрасываем выбранное значение

                // Автоматическое сохранение после выбора лекции
                try {
                    const response = await axiosInstance.post('/zoom_service/update_children_lectures', {
                        parent_id: selectedLecture.id,
                        children_ids: [...duplicateLectures.map(lecture => lecture.id), selectedLectureObj.id],
                    });
                    console.log('Обновленные данные конференции:', response.data);

                    // Обновляем состояние lectures с новыми данными конференции
                    const updatedLectures = lectures.map((lecture) => {
                        if (lecture.id === selectedLecture.id) {
                            return {...lecture,
                                conferenceData: {
                                    ...response.data,
                                    meeting_details: [{...response.data.meeting_details[0], inherited: false}]
                                }
                            };
                        } else if ([...duplicateLectures.map(dl => dl.id), selectedLectureObj.id].includes(lecture.id)) {
                            return {...lecture,
                                conferenceData: {
                                    ...response.data,
                                    meeting_details: [{...response.data.meeting_details[0], inherited: true}]
                                }
                            };
                        }
                        return lecture;
                    });

                    setLectures(updatedLectures);
                    fetchLectures(); // Обновление списка лекций после добавления
                    handleDrawerClose(); // Закрываем боковое окно
                } catch (error) {
                    console.error('Ошибка при обновлении данных лекций:', error);
                }
            }
        }
    };


        const [overlayOpen, setOverlayOpen] = useState(false);
    const [selectedLectureIdForOverlay, setSelectedLectureIdForOverlay] = useState(null); // Новое состояние для ID лекции

    const handleOverlayOpen = (lectureId) => {
        setSelectedLectureIdForOverlay(lectureId);
        setOverlayOpen(true);
    };

    const handleOverlayClose = () => {
        setOverlayOpen(false);
        setSelectedLectureIdForOverlay(null); // Очистка ID лекции при закрытии
    };


    const handleSearchChange = (event) => {
        setSearchQuery(event.target.value);
    };

    const handleLectureRemove = (lecture) => {
        setSelectedChannels((prev) => prev.filter((l) => l !== lecture));
    };

    const fetchUserChannels = async () => {
        try {
            const response = await axiosInstance.post('/user_channels', {}, {
                withCredentials: true,
            });
            console.log('User channels:', response.data.user_channels);
            setChannels(Object.values(response.data.user_channels).map(channel => ({
                id: channel.id,
                name: channel.name,
                tags: channel.tags
            })));
            setChannelsData(response.data.user_channels); // Сохраняем полные данные о каналах
        } catch (error) {
            console.error('Error fetching user channels:', error);
            if (error.response && error.response.status === 401) {
                navigate('/signin');
            }
        }
    };


    const fetchConferenceData = async (conferenceId) => {
        try {
            const response = await axiosInstance.get('/zoom_service/get_conference_data', {
                params: {conference_id: conferenceId},
            });

            console.log('Response Data:', response.data); // Вывод всех данных в консоль

            if (response.data.meeting_details) {
                setInherited(response.data.meeting_details[0].inherited || false);  // Установить состояние наследования

                // Установить каналы с подходящими тегами как выбранные
                const lectureTags = response.data.meeting_details[0].tags || [];
                console.log(`Lecture Tags: ${lectureTags.join(', ')}`);

                // Извлечение children_lecture_ids
                const childrenLectureIds = response.data.meeting_details[0].children_lecture_ids || [];
                console.log(`Children Lecture IDs: ${childrenLectureIds.join(', ')}`);

                const matchedChannels = Object.entries(channelsData).filter(([id, channel]) =>
                    channel.tags.some(tag => lectureTags.includes(tag))
                ).map(([id, channel]) => channel.name); // Используем имя канала
                console.log(`Matched Channels: ${matchedChannels.join(', ')}`);

                setSelectedChannels(matchedChannels);

                return response.data;
            }
        } catch (error) {
            console.error(`Ошибка при получении данных конференции для ID ${conferenceId}:`, error);
        }
        return null;
    };


    const handleDeleteDuplicateLecture = async (parentLectureId, lectureId) => {
        try {
            const response = await axiosInstance.post('/zoom_service/remove_child_lecture', {
                parent_id: parentLectureId,
                child_id: lectureId
            });

            console.log('Удаление прошло успешно:', response.data);
            // Обновите состояние после удаления лекции
            setDuplicateLectures(duplicateLectures.filter(lecture => lecture.id !== lectureId));
            fetchLectures(); // Обновление списка лекций после удаления
            handleDrawerClose(); // Закрываем боковое окно
        } catch (error) {
            console.error('Ошибка при удалении лекции:', error);
        }
    };


    const fetchAllConferencesData = async (conferenceIds) => {
    try {
        const response = await axiosInstance.post('/zoom_service/get_all_conference_data', {
            conference_ids: conferenceIds,
        });

        console.log('Fetched all conference data:', response.data);

        return response.data;
    } catch (error) {
        console.error('Ошибка при получении данных всех конференций:', error);
        return null;
    }
};

const fetchLectures = async () => {
    try {
        const response = await axiosInstance.get('/schedule_service/today_lectures', {
            withCredentials: true,
        });

        // Получаем массив всех conference_id из данных лекций
        const conferenceIds = response.data.map((lecture) => lecture.id);

        // Получаем данные для всех конференций
        const allConferenceData = await fetchAllConferencesData(conferenceIds);

        if (allConferenceData) {
            // Обновляем каждую лекцию соответствующими данными конференции
            const lecturesWithConferenceData = response.data.map((lecture) => ({
                ...lecture,
                conferenceData: allConferenceData[lecture.id], // Соответствие данных конференции по ID
            }));

            setLectures(lecturesWithConferenceData);
        }
    } catch (error) {
        console.error('Ошибка при получении данных:', error);
        if (error.response && error.response.status === 401) {
            navigate('/signin');
        }
    }
};

    useEffect(() => {
        if (channels.length > 0 && selectedLecture) {
            const lectureTags = selectedLecture.conferenceData?.meeting_details[0].tags || [];
            console.log(`Lecture Tags: ${lectureTags.join(', ')}`);

            channels.forEach(channel => {
                console.log(`Channel Name: ${channel.name}, Tags: ${channel.tags.join(', ')}`);
            });

            const matchedChannels = channels.filter(channel =>
                channel.tags.some(tag => lectureTags.includes(tag))
            ).map(channel => channel.name);
            console.log(`Matched Channels: ${matchedChannels.join(', ')}`);

            setSelectedChannels(matchedChannels);
        }
    }, [channels, selectedLecture]);

    useEffect(() => {
        if (selectedLecture && selectedLecture.conferenceData && selectedLecture.conferenceData.childrenLectures) {
            setDuplicateLectures(selectedLecture.conferenceData.childrenLectures);
        }
    }, [selectedLecture]);


    useEffect(() => {
        const autoAddLectures = () => {
            const autoLectures = lectures.filter(lecture => autoDuplicateLectureIds.includes(lecture.id));
            setDuplicateLectures(autoLectures);
        };

        if (lectures.length > 0) {
            autoAddLectures();
        }
    }, [lectures]);

    useEffect(() => {
        if (selectedLecture && selectedLecture.conferenceData && selectedLecture.conferenceData.childrenLectures) {
            setDuplicateLectures(selectedLecture.conferenceData.childrenLectures);
        }
    }, [selectedLecture]);


    useEffect(() => {
        const fetchLecturesAndChannels = async () => {
            await fetchLectures();
            await fetchUserChannels();
        };

        fetchLecturesAndChannels();
    }, [navigate]);

    useEffect(() => {
        const handleSwipe = (e) => {
            if (e.deltaX > 50) { // Чувствительность свайпа
                handleDrawerClose();
            }
        };

        const drawer = document.querySelector('.MuiDrawer-paper');
        if (drawer) {
            drawer.addEventListener('swiped-right', handleSwipe);
        }

        return () => {
            if (drawer) {
                drawer.removeEventListener('swiped-right', handleSwipe);
            }
        };
    }, []);

    const groupLecturesByConference = (lectures) => {
        const groupedLectures = {};

        lectures.forEach(lecture => {
            const conferenceKey = lecture.conferenceData ? lecture.conferenceData.meeting_details[0].conference_key : lecture.id;
            if (!groupedLectures[conferenceKey]) {
                groupedLectures[conferenceKey] = {
                    main: [],
                    inherited: []
                };
            }

            if (lecture.conferenceData?.meeting_details[0].inherited) {
                groupedLectures[conferenceKey].inherited.push(lecture);
            } else {
                groupedLectures[conferenceKey].main.push(lecture);
            }
        });

        return groupedLectures;
    };


    const handleCardClick = async (lecture, isNested = false) => {
        console.log('Selected Lecture:', lecture); // Вывод информации о выбранной лекции в консоль

        setSelectedLecture(lecture);
        setInherited(lecture.conferenceData && lecture.conferenceData.meeting_details[0].inherited); // Установить наследованность

        setEditValues({
            stream: lecture.stream,
            topic: lecture.topic,
            time: lecture.time,
            speaker: lecture.speaker,
            description: lecture.description,
            zoom: lecture.zoom,
        });

        // Вывести все существующие лекции в консоль
        console.log('All Lectures:', lectures);

        let childrenLectureIds = [];

        if (lecture.conferenceData) {
            updateNoteContent(lecture.conferenceData);
            childrenLectureIds = lecture.conferenceData.meeting_details[0].children_lecture_ids || [];
        } else {
            const conferenceData = await fetchConferenceData(lecture.id);
            if (conferenceData) {
                updateNoteContent(conferenceData);
                childrenLectureIds = conferenceData.meeting_details[0].children_lecture_ids || [];
            } else {
                setNoteContent({upperText: '', lowerText: ''});
            }
        }

        // Преобразовать значения children_lecture_ids в int
        const intChildrenLectureIds = childrenLectureIds.map(id => parseInt(id, 10));
        console.log('Children Lecture IDs:', intChildrenLectureIds);

        // Найти лекции по ID
        const testLectures = lectures.filter(lecture => intChildrenLectureIds.includes(lecture.id));

        if (testLectures.length > 0) {
            setDuplicateLectures(testLectures);
        } else {
            console.error('Lectures not found');
        }

        setIsEditing(false);
    };


    const handleDrawerClose = () => {
        setSelectedLecture(null);
    };

    const handleEditClick = () => {
        if (!inherited) { // Только если не унаследовано
            setIsEditing(true);
        }
    };

    const handleInputChange = (e) => {
        const {name, value} = e.target;
        setEditValues((prevValues) => ({
            ...prevValues,
            [name]: value
        }));
    };

    const handleSaveClick = async () => {
        try {
            const response = await axiosInstance.put('/schedule_service/update_lecture', {
                id: selectedLecture.id,
                ...editValues
            });
            console.log(response.data); // Сохранение изменений

            // После сохранения изменений запросите обновленные данные
            fetchLectures();

            setIsEditing(false);
        } catch (error) {
            console.error('Ошибка при сохранении изменений:', error);
        }
    };

    const handleResetClick = () => {
        setOpenConfirmDialog(true);
    };

    const handleConfirmReset = async () => {
        try {
            const response = await axiosInstance.post('/schedule_service/reset_lecture', {
                id: selectedLecture.id,
            });
            console.log(response.data); // Сброс изменений

            // После сброса изменений запросите обновленные данные
            fetchLectures();

            setOpenConfirmDialog(false);
            setSelectedLecture(null);
        } catch (error) {
            console.error('Ошибка при сбросе изменений:', error);
        }
    };


    const handleCancelReset = () => {
        setOpenConfirmDialog(false);
    };

    const handleCreateConference = async (forceRecreate = false) => {
        if (selectedLecture) {
            try {
                setLoadingCreate(true);
                const response = await axiosInstance.post('/zoom_service/create_meet', {
                    conference_id: selectedLecture.id,
                    force_recreate: forceRecreate,
                });
                console.log(response.data);

                if (response.data.status === 'success') {
                    const detailsResponse = await axiosInstance.get('/zoom_service/get_conference_data', {
                        params: {conference_id: selectedLecture.id}
                    });
                    console.log(detailsResponse.data);
                    updateNoteContent(detailsResponse.data);
                    setLectures((prevLectures) =>
                        prevLectures.map((lecture) =>
                            lecture.id === selectedLecture.id
                                ? {...lecture, conferenceData: detailsResponse.data}
                                : lecture
                        )
                    );

                    const updatedConferenceData = await fetchConferenceData(selectedLecture.id);
                    setSelectedLecture(prevLecture => ({
                        ...prevLecture,
                        conferenceData: updatedConferenceData
                    }));

                    await fetchUserChannels();
                }
            } catch (error) {
                console.error('Ошибка при создании конференции', error);
            } finally {
                setLoadingCreate(false);
            }
        }
    };


    const handleLectureMenuClick = (event) => {
        setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
    };

    const handleRecreateClick = () => {
        setOpenRecreateDialog(true);
        setAnchorEl(null);
    };


    const handleRecreateConfirm = async () => {
        if (recreateConfirm === 'ПЕРЕСОЗДАТЬ') {
            try {
                setLoadingRecreate(true);
                await handleCreateConference(true);  // Передаем true для пересоздания
            } catch (error) {
                console.error('Ошибка при пересоздании конференции:', error);
            } finally {
                setLoadingRecreate(false);
                setOpenRecreateDialog(false);
            }
        } else {
            setRecreateConfirm('');
            const dialog = document.getElementById('recreate-dialog');
            if (dialog) {
                dialog.style.animation = 'shake 0.5s';
                setTimeout(() => {
                    dialog.style.animation = '';
                }, 500);
            }
        }
    };

    const updateNoteContent = (responseData) => {
        if (!responseData || !responseData.meeting_details || !responseData.meeting_details.length) {
            setNoteContent({upperText: '', lowerText: ''});
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

        // Обновляем каналы после обновления заметки
        fetchUserChannels();
    };

    const handleAddDuplicateLecture = () => {
        if (selectedDuplicateLecture) {
            const selectedLectureObj = lectures.find(lecture => lecture.id === selectedDuplicateLecture);
            if (selectedLectureObj) {
                setDuplicateLectures([...duplicateLectures, selectedLectureObj]);
                setSelectedDuplicateLecture('');
            }
        }
    };


    const groupedLectures = groupLecturesByConference(lectures);

    const handleMenuClick = (menu) => {
        setSelectedMenu(menu);
        setDrawerOpen(false);  // Закрываем меню после выбора пункта
    };

    const toggleDrawer = () => {
        setDrawerOpen(!drawerOpen);
    };

    // Update the render section to include the new ActionField component

    return (


        <Box sx={{display: 'flex', minHeight: '100vh'}}>

            <WhiteOverlay open={overlayOpen} onClose={handleOverlayClose} lectureId={selectedLectureIdForOverlay} />

            {/* AppBar для маленьких экранов */}
            <AppBar position="fixed" sx={{display: {xs: 'block', md: 'none'}, backgroundColor: '#2196f3'}}>
                <Toolbar sx={{display: 'flex', justifyContent: 'space-between'}}>
                    <IconButton edge="start" color="inherit" aria-label="menu" onClick={toggleDrawer}>
                        <MenuIcon/>
                    </IconButton>
                    <Typography variant="h6">Сегодня</Typography>
                    <IconButton
                        edge="end"
                        color="inherit"
                        aria-label="close"
                        onClick={toggleDrawer}
                        sx={{display: drawerOpen ? 'block' : 'none'}}
                    >
                        <CloseIcon/>
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
            width: {xs: '100%', md: 350},
            boxSizing: 'border-box',
            transition: 'transform 0.3s ease-out',
            position: {xs: 'fixed', md: 'fixed'}, // Изменено на fixed для фиксации
            height: {xs: 'auto', md: '100%'},
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
        },
    }}
>
                <List>
                    <ListItem button onClick={() => navigate('/account')}>
                        <ListItemIcon>
                            <img src={accountIcon} alt="Account" style={{width: 24, height: 24}}/>
                        </ListItemIcon>
                        <ListItemText primary="Аккаунт"/>
                    </ListItem>
                    <Divider/>
                    <ListItem button onClick={() => navigate('/lectures')}>
                        <ListItemIcon>
                            <img src={sheetsIcon} alt="Sheets расписания" style={{width: 24, height: 24}}/>
                        </ListItemIcon>
                        <ListItemText primary="Sheets расписания"/>
                    </ListItem>
                    <Divider/>
                    <ListItem button onClick={() => navigate('/telegram_channels')}>
                        <ListItemIcon>
                            <img src={telegramIcon} alt="Telegram каналы" style={{width: 24, height: 24}}/>
                        </ListItemIcon>
                        <ListItemText primary="Telegram каналы"/>
                    </ListItem>
                    <Divider/>
                    <ListItem button onClick={() => navigate('/lms_streams')}>
                        <ListItemIcon>
                            <img src={mdsIcon} alt="LMS наборы" style={{width: 24, height: 24}}/>
                        </ListItemIcon>
                        <ListItemText primary="LMS наборы"/>
                    </ListItem>
                </List>
                {/* Нижнее меню для больших экранов */}
                <Box sx={{display: {xs: 'none', md: 'block'}, mt: 'auto'}}>
                    <BottomNavBar activePage="/moderator/lectures/today"/>
                </Box>
            </Drawer>

            {/* Контент */}
            <Box
    component="main"
    sx={{
        flexGrow: 1,
        display: 'flex',
        justifyContent: 'center',
        paddingBottom: '84px', // Добавленный отступ в нижней части для меню
        marginLeft: { xs: 0, md: '350px' }, // Добавьте этот отступ для сдвига вправо на ширину бокового меню
    }}
>
                <Container component="main" maxWidth="md">

                    <TitleBox>
                        <Typography component="h1" variant="h5">
                            Сегодня
                        </Typography>
                    </TitleBox>


                    <Box sx={{display: 'flex', minHeight: '100vh', flexDirection: 'column', marginBottom: '84px', marginTop: '10px'}}>

                        {Object.keys(groupedLectures).length > 0 ? (
                            Object.keys(groupedLectures).map((conferenceKey) => (
                                <StyledCard key={conferenceKey}
                                            onClick={() => handleCardClick(groupedLectures[conferenceKey].main[0], false)}>
                                    <CardHeader
                                        title={groupedLectures[conferenceKey].main[0].sheet_name}
                                        titleTypographyProps={{variant: 'h6'}}
                                    />
                                    <CardContent>
                                        <Box display="flex" alignItems="center" mb={1}>
                                            <Book sx={{mr: 1}}/>
                                            <Typography variant="body1">
                                                <strong>Поток:</strong> {groupedLectures[conferenceKey].main[0].stream}
                                            </Typography>
                                        </Box>
                                        {!groupedLectures[conferenceKey].main[0].conferenceData?.meeting_details[0].inherited && (
                                            <>
                                                <Box display="flex" alignItems="center" mb={1}>
                                                    <Info sx={{mr: 1}}/>
                                                    <Typography variant="body1">
                                                        <strong>Тема:</strong> {groupedLectures[conferenceKey].main[0].topic}
                                                    </Typography>
                                                </Box>
                                                <Box display="flex" alignItems="center" mb={1}>
                                                    <AccessTime sx={{mr: 1}}/>
                                                    <Typography variant="body1">
                                                        <strong>Время:</strong> {groupedLectures[conferenceKey].main[0].time}
                                                    </Typography>
                                                </Box>
                                                <Box display="flex" alignItems="center" mb={1}>
                                                    <Person sx={{mr: 1}}/>
                                                    <Typography variant="body1">
                                                        <strong>Спикер:</strong> {groupedLectures[conferenceKey].main[0].speaker}
                                                    </Typography>
                                                </Box>
                                                {groupedLectures[conferenceKey].main[0].description && (
                                                    <Box display="flex" alignItems="center" mb={1}>
                                                        <Description sx={{mr: 1}}/>
                                                        <Typography variant="body1">
                                                            <strong>Описание:</strong> {groupedLectures[conferenceKey].main[0].description}
                                                        </Typography>
                                                    </Box>
                                                )}
                                                <Box display="flex" alignItems="center" mb={1}>
                                                    <Duo sx={{mr: 1}}/>
                                                    <Typography variant="body1">
                                                        <strong>Zoom:</strong> {groupedLectures[conferenceKey].main[0].zoom}
                                                    </Typography>
                                                </Box>
                                            </>
                                        )}
                                        {groupedLectures[conferenceKey].inherited.map((nestedLecture, nestedIndex) => (
                                            <NestedCard key={nestedIndex} onClick={(e) => {
                                                e.stopPropagation();  // Предотвращает всплытие события на родительскую карточку
                                                handleCardClick(nestedLecture, true);
                                            }}>
                                                <CardHeader
                                                    title={nestedLecture.sheet_name}
                                                    titleTypographyProps={{variant: 'h6'}}
                                                />
                                                <CardContent>
                                                    <Box display="flex" alignItems="center" mb={1}>
                                                        <Book sx={{mr: 1}}/>
                                                        <Typography variant="body1">
                                                            <strong>Поток:</strong> {nestedLecture.stream}
                                                        </Typography>
                                                    </Box>
                                                    <Box display="flex" alignItems="center" mb={1}>
                                                        <Info sx={{mr: 1}}/>
                                                        <Typography variant="body1">
                                                            <strong>Тема:</strong> {nestedLecture.topic}
                                                        </Typography>
                                                    </Box>
                                                    <Box display="flex" alignItems="center" mb={1}>
                                                        <AccessTime sx={{mr: 1}}/>
                                                        <Typography variant="body1">
                                                            <strong>Время:</strong> {nestedLecture.time}
                                                        </Typography>
                                                    </Box>
                                                    <Box display="flex" alignItems="center" Custom={1}>
                                                        <Person sx={{mr: 1}}/>
                                                        <Typography variant="body1">
                                                            <strong>Спикер:</strong> {nestedLecture.speaker}
                                                        </Typography>
                                                    </Box>
                                                    {nestedLecture.description && (
                                                        <Box display="flex" alignItems="center" mb={1}>
                                                            <Description sx={{mr: 1}}/>
                                                            <Typography variant="body1">
                                                                <strong>Описание:</strong> {nestedLecture.description}
                                                            </Typography>
                                                        </Box>
                                                    )}
                                                    <Box display="flex" alignItems="center" mb={1}>
                                                        <Duo sx={{mr: 1}}/>
                                                        <Typography variant="body1">
                                                            <strong>Zoom:</strong> {nestedLecture.zoom}
                                                        </Typography>
                                                    </Box>
                                                </CardContent>
                                            </NestedCard>
                                        ))}
                                    </CardContent>
                                    <ZoomIcon src={ZoomLogoGray}
                                              isColored={Boolean(groupedLectures[conferenceKey].main[0].conferenceData)}
                                    />

                                    <ZoomIcon
    src={ZoomLogoGray}
    isColored={Boolean(groupedLectures[conferenceKey].main[0].conferenceData)}
/>

<VideoIconButton
                            isColored={Boolean(groupedLectures[conferenceKey].main[0].conferenceData)}
                            disabled={!Boolean(groupedLectures[conferenceKey].main[0].conferenceData)}
                            onClick={(event) => {
                                event.stopPropagation(); // Останавливаем всплытие события клика
                                handleOverlayOpen(groupedLectures[conferenceKey].main[0].id); // Передача ID лекции
                            }}
                        >
                            <VideoLibraryIcon />
                        </VideoIconButton>


                                </StyledCard>
                            ))
                        ) : (
                            <Typography>Нет лекций на сегодня.</Typography>
                        )}
                    </Box>
                    <CustomDrawer
                        anchor="right"
                        open={Boolean(selectedLecture)}
                        onClose={handleDrawerClose}
                    >
                        <IconButton onClick={handleDrawerClose} sx={{position: 'absolute', top: 11, left: 6}}>
                            <ArrowBackIcon/>
                        </IconButton>
                        {selectedLecture && (
                            <Box sx={{paddingBottom: 5}}>

                                <Typography variant="h6" sx={{textAlign: 'center'}}>Детали лекции</Typography>
                                <Box mt={2}>
                                    {isEditing ? (
                                        <>
                                            <TextField
                                                fullWidth
                                                margin="normal"
                                                label="Поток"
                                                name="stream"
                                                value={editValues.stream}
                                                onChange={handleInputChange}
                                                disabled={inherited}
                                            />
                                            {!inherited && (
                                                <>
                                                    <TextField
                                                        fullWidth
                                                        margin="normal"
                                                        label="Тема"
                                                        name="topic"
                                                        value={editValues.topic}
                                                        onChange={handleInputChange}
                                                    />
                                                    <TextField
                                                        fullWidth
                                                        margin="normal"
                                                        label="Время"
                                                        name="time"
                                                        value={editValues.time}
                                                        onChange={handleInputChange}
                                                    />
                                                    <TextField
                                                        fullWidth
                                                        margin="normal"
                                                        label="Спикер"
                                                        name="speaker"
                                                        value={editValues.speaker}
                                                        onChange={handleInputChange}
                                                    />
                                                    <TextField
                                                        fullWidth
                                                        margin="normal"
                                                        label="Zoom"
                                                        name="zoom"
                                                        value={editValues.zoom}
                                                        onChange={handleInputChange}
                                                    />
                                                </>
                                            )}
                                            <TextField
                                                fullWidth
                                                margin="normal"
                                                label="Описание"
                                                name="description"
                                                value={editValues.description}
                                                onChange={handleInputChange}
                                                disabled={inherited}
                                            />
                                            {!inherited && (
                                                <>
                                                    <CenteredButton onClick={handleSaveClick}>
                                                        Сохранить
                                                    </CenteredButton>
                                                    <CenteredButton onClick={handleResetClick}>
                                                        Сбросить изменения
                                                    </CenteredButton>
                                                </>
                                            )}
                                        </>
                                    ) : (
                                        <>
                                            <Box
                                                sx={{
                                                    border: '1px solid #1976d2',
                                                    borderRadius: '4px',
                                                    padding: '8px',
                                                    marginBottom: '16px',
                                                    cursor: !inherited ? 'pointer' : 'default',
                                                    '&:hover': {
                                                        borderColor: !inherited ? '#1565c0' : '#1976d2',
                                                    }
                                                }}
                                                onClick={!inherited ? handleEditClick : null}
                                            >
                                                <Typography
                                                    variant="body1"><strong>Поток:</strong> {selectedLecture.stream}
                                                </Typography>
                                            </Box>
                                            {!inherited && (
                                                <>
                                                    <Box
                                                        sx={{
                                                            border: '1px solid #1976d2',
                                                            borderRadius: '4px',
                                                            padding: '8px',
                                                            marginBottom: '16px',
                                                            cursor: !inherited ? 'pointer' : 'default',
                                                            '&:hover': {
                                                                borderColor: !inherited ? '#1565c0' : '#1976d2',
                                                            }
                                                        }}
                                                        onClick={!inherited ? handleEditClick : null}
                                                    >
                                                        <Typography
                                                            variant="body1"><strong>Тема:</strong> {selectedLecture.topic}
                                                        </Typography>
                                                    </Box>
                                                    <Box
                                                        sx={{
                                                            border: '1px solid #1976d2',
                                                            borderRadius: '4px',
                                                            padding: '8px',
                                                            marginBottom: '16px',
                                                            cursor: !inherited ? 'pointer' : 'default',
                                                            '&:hover': {
                                                                borderColor: !inherited ? '#1565c0' : '#1976d2',
                                                            }
                                                        }}
                                                        onClick={!inherited ? handleEditClick : null}
                                                    >
                                                        <Typography
                                                            variant="body1"><strong>Время:</strong> {selectedLecture.time}
                                                        </Typography>
                                                    </Box>
                                                    <Box
                                                        sx={{
                                                            border: '1px solid #1976d2',
                                                            borderRadius: '4px',
                                                            padding: '8px',
                                                            marginBottom: '16px',
                                                            cursor: !inherited ? 'pointer' : 'default',
                                                            '&:hover': {
                                                                borderColor: !inherited ? '#1565c0' : '#1976d2',
                                                            }
                                                        }}
                                                        onClick={!inherited ? handleEditClick : null}
                                                    >
                                                        <Typography
                                                            variant="body1"><strong>Спикер:</strong> {selectedLecture.speaker}
                                                        </Typography>
                                                    </Box>
                                                </>
                                            )}
                                            <Box
                                                sx={{
                                                    border: '1px solid #1976d2',
                                                    borderRadius: '4px',
                                                    padding: '8px',
                                                    marginBottom: '16px',
                                                }}
                                            >
                                                <Typography
                                                    variant="body1"><strong>Описание:</strong> {selectedLecture.description}
                                                </Typography>
                                            </Box>
                                            {!inherited && (
                                                <Box
                                                    sx={{
                                                        border: '1px solid #1976d2',
                                                        borderRadius: '4px',
                                                        padding: '8px',
                                                        marginBottom: '16px',
                                                        cursor: !inherited ? 'pointer' : 'default',
                                                        '&:hover': {
                                                            borderColor: !inherited ? '#1565c0' : '#1976d2',
                                                        }
                                                    }}
                                                    onClick={!inherited ? handleEditClick : null}
                                                >
                                                    <Typography
                                                        variant="body1"><strong>Zoom:</strong> {selectedLecture.zoom}
                                                    </Typography>
                                                </Box>
                                            )}
                                            <Typography variant="body1"><strong>Расписание:</strong> <a
                                                href={selectedLecture.link} target="_blank" rel="noopener noreferrer">Открыть
                                                в Google Sheets</a></Typography>
                                            <Typography variant="body1"><strong>Номер
                                                строки:</strong> {selectedLecture.row_number}</Typography>
                                            <Typography variant="body1"><strong>ID:</strong> {selectedLecture.id}
                                            </Typography>
                                            <Box
                                                sx={{
                                                    borderBottom: '3px solid gray',
                                                    marginBottom: '16px',
                                                    marginTop: '16px'
                                                }}
                                            />
                                            {!noteContent.upperText && !inherited && (
                                                <CenteredButton onClick={() => handleCreateConference(false)}>
                                                    {loadingCreate ? 'Создание...' : 'Создать конференцию'}
                                                </CenteredButton>
                                            )}
                                        </>
                                    )}
                                </Box>
                                {noteContent.upperText && !inherited && (
                                    <>
                                        <Box mt={2} p={2} border="1px solid #1976d2" borderRadius="4px"
                                             position="relative">
                                            <Typography variant="h6">Сообщение в чат</Typography>
                                            <CustomMessageBox>
                                                <MessageBox
                                                    position={'right'}
                                                    type={'text'}
                                                    text={noteContent.lowerText}/>
                                            </CustomMessageBox>

                                            {!inherited && (
                                                <>
                                                    <IconButton
                                                        aria-label="more"
                                                        aria-controls="note-menu"
                                                        aria-haspopup="true"
                                                        onClick={handleLectureMenuClick}
                                                        style={{position: 'absolute', top: 8, right: 8}}
                                                    >
                                                        <MoreVert/>
                                                    </IconButton>
                                                    <Menu
                                                        id="note-menu"
                                                        anchorEl={anchorEl}
                                                        keepMounted
                                                        open={Boolean(anchorEl)}
                                                        onClose={handleMenuClose}
                                                    >
                                                        <MenuItem onClick={handleRecreateClick}>Пересоздать
                                                            конференцию</MenuItem>
                                                        <MenuItem onClick={handleDeleteClick}>Удалить
                                                            конференцию</MenuItem>
                                                    </Menu>


                                                    <ActionField>
                                                        <CopyToClipboard text={noteContent.lowerText}>
                                                            <CopyButton>
                                                                <FileCopy/>
                                                            </CopyButton>
                                                        </CopyToClipboard>
                                                        <ChannelSelectBox>
                                                            <ChannelAutocomplete
                                                                multiple
                                                                options={channels.map(channel => channel.name)}
                                                                value={selectedChannels}
                                                                onChange={handleChannelChange}
                                                                filterSelectedOptions
                                                                renderInput={(params) => (
                                                                    <TextField {...params} variant="outlined"
                                                                               placeholder="Выберите канал"
                                                                               label="Telegram канал(ы) лекции"/>
                                                                )}
                                                                renderTags={(value, getTagProps) =>
                                                                    value.map((option, index) => {
                                                                        const tagProps = getTagProps({index});
                                                                        const {key, ...otherProps} = tagProps; // Убираем key из spread-оператора
                                                                        return (
                                                                            <SelectedChannelChip
                                                                                key={key}
                                                                                variant="outlined"
                                                                                label={option}
                                                                                {...otherProps}
                                                                                onDelete={() => handleChannelDelete(option)}
                                                                            />
                                                                        );
                                                                    })
                                                                }
                                                            />

                                                        </ChannelSelectBox>
                                                        <SendButton
                                                            aria-label="send"
                                                            onClick={() => setOpenModal(true)}
                                                        >
                                                            <SendIcon/>
                                                        </SendButton>
                                                    </ActionField>

                                                </>
                                            )}
                                        </Box>
                                    </>
                                )}
                                {noteContent.upperText && !inherited && (
                                    <DuplicateContainer>
                                        <Box display="flex" alignItems="center" mb={2}>
                                            <Typography variant="body2">
                                                Также, сделать конференцией для...
                                            </Typography>
                                            <Tooltip
                                                title="Инструмент для дублирования данных конференции в другие лекции. Если необходимо объединить в одну конференцию несколько потоков или тарифов">
                                                <IconButton>
                                                    <InfoOutlined/>
                                                </IconButton>
                                            </Tooltip>
                                        </Box>
                                        <Box mb={2}>
                                            <Select
                                                fullWidth
                                                value={selectedDuplicateLecture}
                                                onChange={handleLectureSelect}
                                                displayEmpty
                                            >
                                                <MenuItem value="" disabled>
                                                    Выберите лекцию
                                                </MenuItem>
                                                {lectures
                                                    .filter(lecture => !lecture.conferenceData && !duplicateLectures.some(dupLecture => dupLecture.id === lecture.id))
                                                    .map((lecture) => (
                                                        <MenuItem key={lecture.id} value={lecture.id}>
                                                            {lecture.sheet_name} - {lecture.stream} - {lecture.id}
                                                        </MenuItem>
                                                    ))}
                                            </Select>


                                        </Box>
                                        {duplicateLectures.length > 0 && (
                                            <DuplicatedLectures>
                                                {duplicateLectures.map((lecture) => (
                                                    <Box key={lecture.id} display="flex" justifyContent="space-between"
                                                         alignItems="center" mb={1}>
                                                        <Typography
                                                            variant="body2">{lecture.sheet_name} - {lecture.stream} - {lecture.id}</Typography>
                                                        <IconButton
                                                            onClick={() => handleDeleteDuplicateLecture(selectedLecture.id, lecture.id)}>
                                                            <ClearIcon/>
                                                        </IconButton>
                                                    </Box>
                                                ))}
                                            </DuplicatedLectures>
                                        )}

                                    </DuplicateContainer>
                                )}

                            </Box>
                        )}
                    </CustomDrawer>
                    <Dialog
                        id="delete-dialog"
                        open={openDeleteDialog}
                        onClose={handleDeleteDialogClose}
                        aria-labelledby="delete-dialog-title"
                        aria-describedby="delete-dialog-description"
                    >
                        <DialogTitle id="delete-dialog-title">Подтвердите удаление конференции</DialogTitle>
                        <DialogContent>
                            <DialogContentText id="delete-dialog-description">
                                Вы уверены, что хотите удалить конференцию? Это действие нельзя отменить.
                                Для подтверждения введите слово "УДАЛИТЬ".
                            </DialogContentText>
                            <ErrorTextField
                                fullWidth
                                margin="normal"
                                label="Подтверждение"
                                value={deleteConfirm}
                                onChange={(e) => setDeleteConfirm(e.target.value)}
                                error={deleteConfirm && deleteConfirm !== 'УДАЛИТЬ'}
                            />
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={handleDeleteDialogClose} color="primary">
                                Отменить
                            </Button>
                            <Button
                                onClick={handleDeleteConfirm}
                                color="primary"
                                autoFocus
                            >
                                {loadingDelete ? 'Удаление...' : 'Подтвердить'}
                            </Button>
                        </DialogActions>
                    </Dialog>


                    <Dialog
                        open={openConfirmDialog}
                        onClose={handleCancelReset}
                        aria-labelledby="confirm-dialog-title"
                        aria-describedby="confirm-dialog-description"
                    >
                        <DialogTitle id="confirm-dialog-title">Подтвердите сброс изменений</DialogTitle>
                        <DialogContent>
                            <DialogContentText id="confirm-dialog-description">
                                Вы уверены, что хотите сбросить изменения? Это действие нельзя отменить.
                            </DialogContentText>
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={handleCancelReset} color="primary">
                                Отменить
                            </Button>
                            <Button onClick={handleConfirmReset} color="primary" autoFocus>
                                Подтвердить
                            </Button>
                        </DialogActions>
                    </Dialog>

                    <Dialog
                        id="recreate-dialog"
                        open={openRecreateDialog}
                        onClose={() => setOpenRecreateDialog(false)}
                        aria-labelledby="recreate-dialog-title"
                        aria-describedby="recreate-dialog-description"
                    >
                        <DialogTitle id="recreate-dialog-title">Подтвердите пересоздание конференции</DialogTitle>
                        <DialogContent>
                            <DialogContentText id="recreate-dialog-description">
                                Вы уверены, что хотите пересоздать конференцию? Текущая конференция будет удалена.
                                Для того, чтобы пересоздать, введите слово "ПЕРЕСОЗДАТЬ".
                            </DialogContentText>
                            <ErrorTextField
                                fullWidth
                                margin="normal"
                                label="Подтверждение"
                                value={recreateConfirm}
                                onChange={(e) => setRecreateConfirm(e.target.value)}
                                error={recreateConfirm && recreateConfirm !== 'ПЕРЕСОЗДАТЬ'}
                            />
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={() => setOpenRecreateDialog(false)} color="primary">
                                Отменить
                            </Button>
                            <Button
                                onClick={handleRecreateConfirm}
                                color="primary"
                                autoFocus
                            >
                                {loadingRecreate ? 'Пересоздание...' : 'Подтвердить'}
                            </Button>
                        </DialogActions>
                    </Dialog>

                    {/* Модальное окно */}
                    <Dialog
                        open={openModal}
                        onClose={() => setOpenModal(false)}
                        aria-labelledby="modal-title"
                        aria-describedby="modal-description"
                        fullWidth
                        maxWidth="md"
                    >
                        <DialogTitle id="modal-title">Модальное окно</DialogTitle>
                        <DialogContent>
                            <DialogContentText id="modal-description">
                                Содержимое модального окна.
                            </DialogContentText>
                        </DialogContent>
                        <DialogActions>
                            <Button onClick={() => setOpenModal(false)} color="primary">
                                Закрыть
                            </Button>
                        </DialogActions>
                    </Dialog>
                </Container>

                {/* Добавляем Snackbar для уведомлений */}
                <Snackbar
                    open={snackbarOpen}
                    autoHideDuration={6000}
                    onClose={() => setSnackbarOpen(false)}
                    message={snackbarMessage}
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
                />

            </Box>

            {/* Нижнее меню для маленьких экранов */}
            <Box sx={{display: {xs: 'block', md: 'none'}, position: 'fixed', bottom: 0, width: '100%'}}>
                <BottomNavBar activePage="/moderator/lectures/archive"/>
            </Box>
        </Box>
    );
}





