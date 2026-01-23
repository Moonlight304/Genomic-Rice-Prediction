import { useEffect, useState } from 'react';
import API from '../api/axios';
import { 
    Calendar, MapPin, ChevronDown, ChevronUp, Clock, History as HistoryIcon,
    CloudRain, Thermometer, Droplets, Beaker
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface PredictionRecord {
    _id: string;
    sample_name: string;
    timestamp: string;
    location: {
        lat: number;
        lon: number;
    };
    environmental_data?: {
        rainfall: number;
        temp: number;
        soil_ph: number;
        soil_nitrogen: number;
    };
    results: {
        sample_id: string;
        predicted_days: number;
        confidence: string;
    }[];
}

const History = () => {
    const [history, setHistory] = useState<PredictionRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [expandedId, setExpandedId] = useState<string | null>(null);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const res = await API.get('/history');
                setHistory(res.data);
            } catch (err) {
                console.error("Failed to fetch history", err);
            } finally {
                setLoading(false);
            }
        };

        fetchHistory();
    }, []);

    const toggleExpand = (id: string) => {
        setExpandedId(expandedId === id ? null : id);
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    if (loading) {
        return (
            <div className="min-h-[calc(100vh-4rem)] flex justify-center items-center bg-slate-50">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
            </div>
        );
    }

    return (
        <div className="min-h-[calc(100vh-4rem)] bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-5xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
                            <HistoryIcon className="h-8 w-8 text-emerald-600" />
                            Prediction History
                        </h1>
                        <p className="mt-2 text-slate-600">View your past genomic analyses</p>
                    </div>
                    <Link
                        to="/predict"
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-emerald-600 hover:bg-emerald-700"
                    >
                        New Analysis
                    </Link>
                </div>

                {history.length === 0 ? (
                    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center">
                        <div className="mx-auto h-12 w-12 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                            <HistoryIcon className="h-6 w-6 text-slate-400" />
                        </div>
                        <h3 className="text-lg font-medium text-slate-900">No history found</h3>
                        <p className="mt-1 text-slate-500">You haven't run any analyses yet.</p>
                        <div className="mt-6">
                            <Link to="/predict" className="text-emerald-600 hover:text-emerald-500 font-medium">
                                Start your first analysis &rarr;
                            </Link>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {history.map((record) => (
                            <div key={record._id} className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden hover:border-emerald-200 transition-colors">
                                <div 
                                    className="p-6 cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4"
                                    onClick={() => toggleExpand(record._id)}
                                >
                                    <div className="flex items-start gap-4">
                                        <div className="p-3 bg-emerald-50 rounded-lg">
                                            <Clock className="h-6 w-6 text-emerald-600" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-semibold text-slate-900">{record.sample_name}</h3>
                                            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1 text-sm text-slate-500">
                                                <div className="flex items-center gap-1">
                                                    <Calendar className="h-4 w-4" />
                                                    {formatDate(record.timestamp)}
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <MapPin className="h-4 w-4" />
                                                    {record.location.lat.toFixed(4)}, {record.location.lon.toFixed(4)}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div className="flex items-center justify-between md:justify-end gap-4">
                                        <div className="text-right">
                                            <span className="block text-2xl font-bold text-slate-900">
                                                {record.results.length}
                                            </span>
                                            <span className="text-xs text-slate-500 font-medium uppercase tracking-wide">Samples</span>
                                        </div>
                                        {expandedId === record._id ? (
                                            <ChevronUp className="h-5 w-5 text-slate-400" />
                                        ) : (
                                            <ChevronDown className="h-5 w-5 text-slate-400" />
                                        )}
                                    </div>
                                </div>

                                {expandedId === record._id && (
                                    <div className="border-t border-slate-100 bg-slate-50/50 p-6 animate-fade-in-down">
                                        
                                        {record.environmental_data && (
                                            <div className="mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                                                <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
                                                    <div className="bg-blue-50 p-2 rounded-lg">
                                                        <CloudRain className="h-5 w-5 text-blue-600" />
                                                    </div>
                                                    <div>
                                                        <p className="text-xs text-slate-500 font-medium uppercase">Rainfall</p>
                                                        <p className="text-sm font-bold text-slate-900">{record.environmental_data.rainfall} mm</p>
                                                    </div>
                                                </div>
                                                <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
                                                    <div className="bg-orange-50 p-2 rounded-lg">
                                                        <Thermometer className="h-5 w-5 text-orange-600" />
                                                    </div>
                                                    <div>
                                                        <p className="text-xs text-slate-500 font-medium uppercase">Temperature</p>
                                                        <p className="text-sm font-bold text-slate-900">{record.environmental_data.temp} °C</p>
                                                    </div>
                                                </div>
                                                <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
                                                    <div className="bg-purple-50 p-2 rounded-lg">
                                                        <Beaker className="h-5 w-5 text-purple-600" />
                                                    </div>
                                                    <div>
                                                        <p className="text-xs text-slate-500 font-medium uppercase">Soil pH</p>
                                                        <p className="text-sm font-bold text-slate-900">{record.environmental_data.soil_ph}</p>
                                                    </div>
                                                </div>
                                                <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex items-center gap-3">
                                                    <div className="bg-emerald-50 p-2 rounded-lg">
                                                        <Droplets className="h-5 w-5 text-emerald-600" />
                                                    </div>
                                                    <div>
                                                        <p className="text-xs text-slate-500 font-medium uppercase">Nitrogen</p>
                                                        <p className="text-sm font-bold text-slate-900">{record.environmental_data.soil_nitrogen} g/kg</p>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                                            <table className="min-w-full divide-y divide-slate-200">
                                                <thead className="bg-slate-50">
                                                    <tr>
                                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Sample ID</th>
                                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Result</th>
                                                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Confidence</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="bg-white divide-y divide-slate-200">
                                                    {record.results.map((result, idx) => {
                                                        const isUnsuitable = result.confidence.includes("Unsuitable");
                                                        return (
                                                            <tr key={idx} className={isUnsuitable ? 'bg-red-50/30' : ''}>
                                                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900">
                                                                    {result.sample_id}
                                                                </td>
                                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-900 font-bold">
                                                                    {isUnsuitable ? (
                                                                        <span className="text-red-700">Growth Unviable</span>
                                                                    ) : (
                                                                        `${result.predicted_days} Days`
                                                                    )}
                                                                </td>
                                                                <td className="px-6 py-4 whitespace-nowrap">
                                                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                                                        isUnsuitable 
                                                                            ? 'bg-red-100 text-red-800'
                                                                            : result.confidence === 'High Confidence'
                                                                                ? 'bg-green-100 text-green-800'
                                                                                : 'bg-yellow-100 text-yellow-800'
                                                                    }`}>
                                                                        {result.confidence}
                                                                    </span>
                                                                </td>
                                                            </tr>
                                                        );
                                                    })}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default History;
