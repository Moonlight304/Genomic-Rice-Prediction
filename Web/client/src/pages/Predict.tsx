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

                                            return (
                                                <tr key={idx} className={`transition-colors ${isUnsuitable ? 'bg-red-50/50 hover:bg-red-50' : 'hover:bg-slate-50'}`}>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 border-r border-slate-100">{result.sample_id}</td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-bold border-r border-slate-100">
                                                        {isUnsuitable ? (
                                                            <span className="text-red-700 flex items-center gap-1.5">
                                                                Growth Unviable
                                                            </span>
                                                        ) : (
                                                            `${result.predicted_days} Days`
                                                        )}
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${isUnsuitable
                                                                ? 'bg-red-100 text-red-800 border border-red-200'
                                                                : result.confidence === 'High Confidence'
                                                                    ? 'bg-green-100 text-green-800'
                                                                    : 'bg-yellow-100 text-yellow-800'
                                                            }`}>
                                                            {result.confidence}
                                                        </span>
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
