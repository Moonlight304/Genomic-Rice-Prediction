import React, { useState, useRef, useEffect } from 'react';
import API from '../api/axios';
import { Upload, MapPin, Loader2, AlertCircle, FileText, CheckCircle, BarChart3 } from 'lucide-react';

interface Result {
    sample_id: string;
    predicted_days: number;
    confidence: string;
}

const Predict = () => {
    const [file, setFile] = useState<File | null>(null);
    const [latitude, setLatitude] = useState('');
    const [longitude, setLongitude] = useState('');
    const [month, setMonth] = useState('7');
    const [irrigation, setIrrigation] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [results, setResults] = useState<Result[]>([]);
    const resultsRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (results.length > 0 && resultsRef.current) {
            resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, [results]);
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handlePredict = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) {
            setError('Please upload a CSV file.');
            return;
        }

        setLoading(true);
        setError('');
        setResults([]);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('latitude', latitude);
        formData.append('longitude', longitude);
        formData.append('month', month);
        formData.append('irrigation', irrigation.toString());

        try {
            const response = await API.post('/predict', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setResults(response.data);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.error || 'Prediction failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[calc(100vh-4rem)] bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className={`max-w-7xl mx-auto transition-all duration-500 ${results.length > 0 ? 'grid lg:grid-cols-2 gap-8' : ''}`}>

                {/* Input Section */}
                <div className={`space-y-8 ${results.length === 0 ? 'max-w-3xl mx-auto' : ''}`}>
                    <div className="text-center lg:text-left">
                        <h1 className="text-3xl font-bold text-slate-900">Run Genomic Analysis</h1>
                        <p className="mt-2 text-slate-600">Upload your sample data to generate yield predictions</p>
                    </div>

                    <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 overflow-hidden border border-slate-100">
                        <form onSubmit={handlePredict} className="p-8 space-y-8">

                            {/* Location Section */}
                            <div className="space-y-4">
                                <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                                    <MapPin className="h-5 w-5 text-emerald-600" />
                                    <h2 className="text-lg font-semibold text-slate-800">Location Context</h2>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-slate-700">Latitude</label>
                                        <input
                                            type="number"
                                            step="any"
                                            placeholder="e.g. 23.45"
                                            value={latitude}
                                            onChange={(e) => setLatitude(e.target.value)}
                                            className="block w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all no-spinner"
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-slate-700">Longitude</label>
                                        <input
                                            type="number"
                                            step="any"
                                            placeholder="e.g. 88.21"
                                            value={longitude}
                                            onChange={(e) => setLongitude(e.target.value)}
                                            className="block w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all no-spinner"
                                            required
                                        />
                                    </div>
                                </div>
                                <p className="text-xs text-slate-500">Coordinates are used to retrieve precise soil and environmental data.</p>
                            </div>

                            {/* Agronomic Controls */}
                            <div className="space-y-4">
                                <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                                    <BarChart3 className="h-5 w-5 text-emerald-600" />
                                    <h2 className="text-lg font-semibold text-slate-800">Season & Management</h2>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-slate-700">Sowing Month</label>
                                        <select
                                            value={month}
                                            onChange={(e) => setMonth(e.target.value)}
                                            className="block w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all custom-select"
                                        >
                                            <option value="6">June (Kharif)</option>
                                            <option value="7">July (Kharif)</option>
                                            <option value="11">November (Rabi)</option>
                                            <option value="12">December (Rabi)</option>
                                            <option value="1">January</option>
                                            <option value="2">February</option>
                                            <option value="3">March</option>
                                            <option value="4">April</option>
                                            <option value="5">May</option>
                                            <option value="8">August</option>
                                            <option value="9">September</option>
                                            <option value="10">October</option>
                                        </select>
                                    </div>
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-slate-700">Irrigation Management</label>
                                        <div 
                                            onClick={() => setIrrigation(!irrigation)}
                                            className={`flex items-center justify-between px-4 py-2.5 border rounded-xl cursor-pointer transition-all ${irrigation ? 'bg-emerald-50 border-emerald-200' : 'bg-slate-50 border-slate-200'}`}
                                        >
                                            <span className={`text-sm ${irrigation ? 'text-emerald-700 font-semibold' : 'text-slate-600'}`}>
                                                {irrigation ? 'Irrigation: Optimized' : 'Irrigation: Rainfed'}
                                            </span>
                                            <div className={`w-12 h-6 rounded-full p-1 transition-colors ${irrigation ? 'bg-emerald-500' : 'bg-slate-300'}`}>
                                                <div className={`w-4 h-4 rounded-full bg-white shadow-sm transition-transform ${irrigation ? 'translate-x-6' : 'translate-x-0'}`} />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <p className="text-xs text-slate-500">
                                    {irrigation 
                                        ? "Simulating predicted yield with optimal water availability (1500mm)."
                                        : "Simulating yield based on natural historical rainfall patterns (Last 5 Years avg)."}
                                </p>
                            </div>

                            {/* File Upload Section */}
                            <div className="space-y-4">
                                <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                                    <FileText className="h-5 w-5 text-emerald-600" />
                                    <h2 className="text-lg font-semibold text-slate-800">Genomic Data</h2>
                                </div>

                                <div className="mt-2 flex justify-center px-6 pt-5 pb-6 border-2 border-slate-300 border-dashed rounded-xl hover:bg-slate-50 transition-colors">
                                    <div className="space-y-1 text-center">
                                        <Upload className="mx-auto h-12 w-12 text-slate-400" />
                                        <div className="flex text-sm text-slate-600 justify-center">
                                            <label
                                                htmlFor="file-upload"
                                                className="relative cursor-pointer bg-transparent rounded-md font-medium text-emerald-600 hover:text-emerald-500 focus-within:outline-none"
                                            >
                                                <span>Upload a file</span>
                                                <input id="file-upload" name="file-upload" type="file" className="sr-only" accept=".csv" onChange={handleFileChange} />
                                            </label>
                                            <p className="pl-1">or drag and drop</p>
                                        </div>
                                        <p className="text-xs text-slate-500">CSV up to 10MB</p>
                                        {file && (
                                            <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-sm font-medium">
                                                <CheckCircle className="h-4 w-4" />
                                                {file.name}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {error && (
                                <div className="p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-r-md flex items-start gap-3">
                                    <AlertCircle className="h-5 w-5 mt-0.5" />
                                    <span className="text-sm">{error}</span>
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading || !file}
                                className="w-full flex items-center justify-center py-3 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-xl shadow-lg shadow-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                                {loading ? (
                                    <>
                                        <Loader2 className="h-5 w-5 animate-spin mr-2" />
                                        Processing Analysis...
                                    </>
                                ) : (
                                    "Start Analysis"
                                )}
                            </button>
                        </form>
                    </div>
                </div>

                {/* Results Section */}
                {results.length > 0 && (
                    <div ref={resultsRef} className="space-y-8 animate-fade-in-up">
                        <div className="hidden lg:block text-left h-[88px]"> {/* Spacer to align with title */}
                            <div className="flex items-center gap-3 h-full pb-2">
                                <div className="p-2 bg-emerald-100 rounded-lg">
                                    <BarChart3 className="h-6 w-6 text-emerald-700" />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-bold text-slate-900">Analysis Results</h2>
                                    <p className="text-slate-600">Predictions based on your inputs</p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 overflow-hidden border border-slate-100 lg:h-[calc(100%-7rem)] flex flex-col">
                            <div className="lg:hidden p-6 border-b border-gray-100 bg-emerald-50/50">
                                <h2 className="text-xl font-bold text-slate-800">Analysis Results</h2>
                            </div>
                            <div className="overflow-x-auto custom-scrollbar flex-1">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50 sticky top-0 z-10">
                                        <tr>
                                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sample ID</th>
                                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estimated Maturity</th>
                                            <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {results.map((result, idx) => {
                                            const isUnsuitable = result.confidence.includes("Unsuitable");
                                            const failureReason = isUnsuitable 
                                                ? result.confidence.replace("Unsuitable Environment:", "").trim() 
                                                : "";

                                            return (
                                                <tr key={idx} className={`transition-colors ${isUnsuitable ? 'bg-red-50/50 hover:bg-red-50' : 'hover:bg-slate-50'}`}>
                                                    <td className="px-6 py-6 whitespace-nowrap text-sm font-medium text-gray-900 border-r border-slate-100 align-top">
                                                        {result.sample_id}
                                                    </td>
                                                    <td className="px-6 py-6 whitespace-nowrap text-sm text-gray-900 font-bold border-r border-slate-100 align-top">
                                                        {isUnsuitable ? (
                                                            <span className="text-red-700 flex items-center gap-1.5">
                                                                Growth Unviable
                                                            </span>
                                                        ) : (
                                                            `${result.predicted_days} Days`
                                                        )}
                                                    </td>
                                                    <td className="px-6 py-6 card-zoom">
                                                        <div className={`inline-flex flex-col items-start px-4 py-3 rounded-xl border w-full max-w-sm transition-all ${isUnsuitable
                                                                ? 'bg-red-50 text-red-800 border-red-100 shadow-sm shadow-red-100/50'
                                                                : result.confidence === 'High Confidence'
                                                                    ? 'bg-emerald-50 text-emerald-800 border-emerald-100'
                                                                    : 'bg-amber-50 text-amber-800 border-amber-100'
                                                            }`}>
                                                            {isUnsuitable ? (
                                                                <>
                                                                    <div className="flex items-center gap-2 mb-2 border-b border-red-200/60 pb-2 w-full">
                                                                        <AlertCircle className="w-4 h-4 text-red-600" />
                                                                        <span className="font-bold text-red-700 text-xs uppercase tracking-wider">Environment Failure</span>
                                                                    </div>
                                                                    <p className="text-sm text-red-800/90 leading-relaxed font-medium">
                                                                        {failureReason || "Environmental conditions (Rainfall, Temperature, or Soil Nitrogen) are critical for growth."}
                                                                    </p>
                                                                </>
                                                            ) : (
                                                                <span className="text-sm font-medium">{result.confidence}</span>
                                                            )}
                                                        </div>
                                                    </td>
                                                </tr>
                                            )
                                        })}
                                    </tbody>
                                </table>
                            </div>
                            <div className="p-4 bg-slate-50 border-t border-slate-100 text-center">
                                <p className="text-xs text-slate-500">Analysis completed successfully. {results.length} samples processed.</p>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Predict;
