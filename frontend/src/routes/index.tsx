import {createFileRoute} from '@tanstack/react-router';
import {ForecastPage} from '@/features/forecast/components/ForecastPage';

const Home = () => <ForecastPage />;

export const Route = createFileRoute('/')({
    component: Home,
});
