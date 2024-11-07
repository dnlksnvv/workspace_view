import { styled, keyframes } from '@mui/system';
import { Box } from '@mui/material';
import Typography from "@mui/material/Typography";
import { ReactComponent as SentimentDissatisfiedIcon } from './box.svg';


export const BottomSection = styled(Box)(({ theme }) => ({
    flexGrow: 1,
    borderTop: `1px solid #ccc`,
    marginTop: theme.spacing(2),
    paddingTop: theme.spacing(2),
    position: 'relative',
}));

export const OverlayContainer = styled(Box)(({ theme }) => ({
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    zIndex: 1000,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    maxWidth: '100vw',
    overflow: 'hidden',
}));

export const WhiteBlock = styled(Box)(({ theme }) => ({
    backgroundColor: 'white',
    borderRadius: '15px',
    padding: theme.spacing(4),
    maxWidth: '820px', // Ограничиваем максимальную ширину оверлея
    width: '90%',
    height: '80vh',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between', // Равномерное распределение контента
    [`@media (max-width: 600px)`]: {
        height: 'auto',
        padding: theme.spacing(2),
    },
}));

export const TopSection = styled(Box)(({ theme }) => ({
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing(2),
    marginBottom: theme.spacing(2),
    borderBottom: `1px solid #ccc`,
    paddingBottom: theme.spacing(2),
    alignItems: 'center',
    [`@media (min-width: 600px)`]: {
        flexDirection: 'row',
        alignItems: 'flex-start',
    },
}));

export const VideoBox = styled(Box)(({ theme }) => ({
    width: '100%',
    backgroundColor: '#f0f0f0',
    borderRadius: '15px',
    position: 'relative',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    aspectRatio: '16 / 9',
    borderBottomLeftRadius: 0,
    borderBottomRightRadius: 0,
    [`@media (max-width: 600px)`]: {
        maxHeight: 'calc(100vh - 150px)',
    },
}));


export const VideoContainer = styled(Box)(({ theme }) => ({
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    width: '68%',
    paddingRight: 30,
    paddingLeft: 15,
    [`@media (max-width: 600px)`]: {
        width: '100%',
        marginBottom: theme.spacing(2),
        paddingRight: 0,
        paddingLeft: 0,
    },
}));

export const VideoListBox = styled(Box)(({ theme }) => ({
    width: '100%',
    maxHeight: 'calc((62vw * 9) / 16)',
    overflow: 'hidden',
    backgroundColor: '#f9f9f9',
    borderRadius: '15px',
    padding: theme.spacing(2),
    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.1)',
    display: 'flex',
    flexDirection: 'column',
    position: 'relative',
    [`@media (min-width: 600px)`]: {
        width: '30%',
    },
    [`@media (max-width: 600px)`]: {
        width: 'calc(100% - 32px)',
    },
}));


export const ScrollableCardContainer = styled(Box)(({ theme }) => ({
    flex: 1,
    overflowY: 'auto',
    paddingRight: theme.spacing(1),
    paddingLeft: theme.spacing(1),
    marginRight: '-8px',
    marginLeft: '-8px',

}));

export const RefreshCard = styled(Box)(({ theme }) => ({
    backgroundColor: '#e0e0e0',
    padding: theme.spacing(2),
    marginBottom: theme.spacing(2),
    borderRadius: '8px',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    cursor: 'pointer',
    '&:hover': {
        backgroundColor: '#d0d0d0',
    },
    [`@media (max-width: 600px)`]: {
        padding: theme.spacing(1),
        '& .MuiTypography-root': {
            fontSize: '0.75rem',
        },
    },
}));

const loadingAnimation = keyframes`
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
`;

export const LoadingPlaceholder = styled(Box)(({ theme }) => ({
    backgroundColor: '#e0e0e0',
    height: '60px',
    marginBottom: theme.spacing(2),
    borderRadius: '8px',
    animation: `${loadingAnimation} 1.5s infinite ease-in-out`,
}));

const dotAnimation = keyframes`
    0%, 20% { opacity: 0; }
    40% { opacity: 1; }
    100% { opacity: 0; }
`;

export const ProcessingText = styled(Typography)`
    font-size: 14px;
    & span {
        animation: ${dotAnimation} 1.5s infinite;
        &:nth-of-type(1) { animation-delay: 0s; }
        &:nth-of-type(2) { animation-delay: 0.2s; }
        &:nth-of-type(3) { animation-delay: 0.4s; }
    }
`;

export const NoRecordsContainer = styled(Box)(({ theme }) => ({
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100%',
    color: theme?.palette?.text?.secondary || 'rgba(0,0,0,0.37)',
}));


export const ControlButtonsContainer = styled(Box)(({ theme }) => ({
    display: 'flex',
    justifyContent: 'flex-end',
    gap: theme.spacing(2),
    marginTop: theme.spacing(2),
}));

export const NoRecordsIcon = styled(SentimentDissatisfiedIcon)(({ theme }) => ({
    width: '50%',
    height: 'auto',
    maxWidth: '200px',
    marginBottom: theme.spacing(2),
    fill: theme?.palette?.text?.secondary || 'rgba(0,0,0,0.37)',
}));

export const NoRecordsText = styled(Typography)(({ theme }) => ({
    fontSize: '1.5rem',
    textAlign: 'center',
    color: theme?.palette?.text?.secondary || 'rgba(0,0,0,0.37)',
    [`@media (max-width: 960px)`]: {
        fontSize: '1.2rem',
    },
    [`@media (max-width: 600px)`]: {
        fontSize: '1rem',
    },
}));


export const TrimContainer = styled(Box)(({ theme }) => ({
    width: 'calc(100% - 32px)', // Уменьшаем ширину на 10 пикселей
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderTopLeftRadius: '0px',
    borderTopRightRadius: '0px',
    borderBottomLeftRadius: '15px',
    borderBottomRightRadius: '15px',
    padding: theme.spacing(2),
    boxShadow: '0px -2px 10px rgba(0, 0, 0, 0.1)',
    [`@media (max-width: 600px)`]: {
        width: 'calc(100% - 16px)',
        padding: theme.spacing(1),
        '& button': {
            fontSize: '0.75rem',
            padding: theme.spacing(0.5, 1),
            minWidth: '50px',
        },
        '& .MuiTypography-root': {
            fontSize: '0.75rem',
        },
    },
}));

