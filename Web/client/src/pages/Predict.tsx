import React, { useState, useRef, useEffect } from 'react';
import API from '../api/axios';
import { Upload, MapPin, Loader2, AlertCircle, FileText, CheckCircle, BarChart3, Map as MapIcon, X, Download } from 'lucide-react';
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import html2canvas from 'html2canvas';

import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

const MapController = ({ onRegister }: { onRegister: (map: L.Map) => void }) => {
    const map = useMap();
    useEffect(() => {
        onRegister(map);
    }, [map, onRegister]);
    return null;
};

interface EnvData {
    E_avg_temp: number;
    E_max_temp: number;
    E_total_rain_mm: number;
    E_solar_radiation: number;
    E_humidity_perc: number;
    E_soil_moisture: number;
    E_soil_ph: number | null;
    E_soil_nitrogen: number | null;
}

interface Result {
    sample_id: string;
    predicted_days: number;
    confidence: string;
}

const LocationMarker = ({
    position,
    setPosition
}: {
    position: { lat: number; lng: number } | null,
    setPosition: (lat: number, lng: number) => void
}) => {
    const map = useMapEvents({
        click(e) {
            setPosition(e.latlng.lat, e.latlng.lng);
            map.flyTo(e.latlng, map.getZoom());
        },
    });

    useEffect(() => {
        if (position) {
            map.flyTo([position.lat, position.lng], map.getZoom());
        }
    }, [position?.lat, position?.lng, map]);

    return position ? <Marker position={[position.lat, position.lng]} /> : null;
};

const Predict = () => {
    const [file, setFile] = useState<File | null>(null);
    const [latitude, setLatitude] = useState('');
    const [longitude, setLongitude] = useState('');
    const [showMap, setShowMap] = useState(false);
    const [month, setMonth] = useState('7');
    const [irrigation, setIrrigation] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [results, setResults] = useState<Result[]>([]);
    const [envData, setEnvData] = useState<EnvData | null>(null);
    const resultsRef = useRef<HTMLDivElement>(null);
    const mapInstance = useRef<L.Map | null>(null);

    const handleMapUpdate = (lat: number, lng: number) => {
        setLatitude(lat.toFixed(4));
        setLongitude(lng.toFixed(4));
    };

    const getMapCenter = (): [number, number] => {
        const lat = parseFloat(latitude);
        const lng = parseFloat(longitude);
        return (!isNaN(lat) && !isNaN(lng)) ? [lat, lng] : [20.5937, 78.9629]; 
    };

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
            if (Array.isArray(response.data)) {
                setResults(response.data);
                setEnvData(null);
            } else {
                setResults(response.data.predictions);
                setEnvData(response.data.environmental_data);
            }
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.error || 'Prediction failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const generatePDF = async () => {
        const doc = new jsPDF();
        const pageWidth = doc.internal.pageSize.getWidth();
        const now = new Date();
        const timestamp = now.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        // 1. BRANDED HEADER
        doc.setFillColor(16, 185, 129);
        doc.rect(0, 0, pageWidth, 40, 'F');

        doc.setTextColor(255, 255, 255);
        doc.setFont("helvetica", "bold");
        doc.setFontSize(22);
        doc.text("Agronomic Analysis Report", 14, 25); 

        doc.setFont("helvetica", "normal");
        doc.setFontSize(10);
        doc.text(timestamp, pageWidth - 14, 25, { align: "right" });
        doc.text("Genomic-Rice-Prediction System", pageWidth - 14, 33, { align: "right" });

        doc.setTextColor(0, 0, 0);
        let yPos = 55;

        // 2. SIMULATION CONFIGURATION
        doc.setFontSize(14);
        doc.setFont("helvetica", "bold");
        doc.setTextColor(30, 41, 59);
        doc.text("Simulation Configuration", 14, yPos);
        yPos += 6;

        const configData = [
            ['Analysis Date', timestamp],
            ['Sample Name', file ? file.name : 'Uploaded Sample'],
            ['Coordinates', `${latitude}, ${longitude}`],
            ['Sowing Month', new Date(0, parseInt(month) - 1).toLocaleString('default', { month: 'long' })],
            ['Irrigation', irrigation ? "ON (Optimized Water)" : "OFF (Rainfed Only)"]
        ];

        autoTable(doc, {
            startY: yPos,
            head: [['Parameter', 'Value']],
            body: configData,
            theme: 'plain',
            styles: { fontSize: 9, cellPadding: 2, textColor: [70, 70, 70] },
            columnStyles: { 0: { fontStyle: 'bold' } },
            margin: { left: 14, right: 14 }
        });

        yPos = (doc as any).lastAutoTable.finalY + 10;

        // 3. MAP SNAPSHOT
        const wasMapVisible = showMap;
        if (!wasMapVisible) {
            setShowMap(true);
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        if (mapInstance.current) {
            const centerLat = parseFloat(latitude);
            const centerLon = parseFloat(longitude);
            if (!isNaN(centerLat) && !isNaN(centerLon)) {
                mapInstance.current.setView([centerLat, centerLon], 10, { animate: false });
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }

        const mapElement = document.getElementById('map-capture');
        if (mapElement) {
            try {
                const canvas = await html2canvas(mapElement, {
                    useCORS: true,
                    logging: false,
                    allowTaint: true
                });
                const imgData = canvas.toDataURL('image/png');

                const imgWidth = 180;
                const imgHeight = (canvas.height * imgWidth) / canvas.width;
                const displayHeight = Math.min(imgHeight, 60);

                doc.setDrawColor(220, 220, 220);
                doc.rect(14, yPos, imgWidth + 2, displayHeight + 2);
                doc.addImage(imgData, 'PNG', 15, yPos + 1, imgWidth, displayHeight);
                yPos += displayHeight + 10;
            } catch (e) {
                console.error("Map capture failed", e);
            }
        }

        if (!wasMapVisible) {
            setShowMap(false);
        }

        // 4. ENVIRONMENTAL PROFILING
        if (envData) {
            doc.setFontSize(14);
            doc.setFont("helvetica", "bold");
            doc.setTextColor(30, 41, 59);
            doc.text("Environmental Profile", 14, yPos);
            yPos += 5;

            const tableData = [
                ['Avg Temperature', `${envData.E_avg_temp} °C`, 'Daily Mean'],
                ['Total Rainfall', `${envData.E_total_rain_mm} mm`, irrigation ? 'Artificial Target' : 'Natural 5y Avg'],
                ['Soil pH', envData.E_soil_ph !== null ? envData.E_soil_ph : 'N/A', 'Level'],
                ['Soil Nitrogen', envData.E_soil_nitrogen !== null ? `${envData.E_soil_nitrogen} g/kg` : 'N/A', 'Nutrient Content'],
                ['Solar Radiation', `${envData.E_solar_radiation} MJ/m²`, 'Energy']
            ];

            autoTable(doc, {
                startY: yPos,
                head: [['Parameter', 'Value', 'Context']],
                body: tableData,
                theme: 'grid',
                headStyles: { fillColor: [16, 185, 129], textColor: 255, fontSize: 10 },
                styles: { fontSize: 10, cellPadding: 4 },
                margin: { left: 14, right: 14 }
            });

            yPos = (doc as any).lastAutoTable.finalY + 15;
        }

        // 5. CERTIFICATE OF VIABILITY
        doc.addPage();
        yPos = 20;

        const isViable = results.length > 0 && !results[0].confidence.includes("Unsuitable");

        const color = isViable ? [16, 185, 129] : [220, 38, 38];
        const bg = isViable ? [236, 253, 245] : [254, 242, 242];

        doc.setDrawColor(color[0], color[1], color[2]);
        doc.setFillColor(bg[0], bg[1], bg[2]);
        doc.roundedRect(14, yPos, 182, 35, 3, 3, 'FD');

        doc.setFontSize(14);
        doc.setFont("helvetica", "bold");
        doc.setTextColor(color[0], color[1], color[2]);
        doc.text(isViable ? "CERTIFICATE: VIABLE FOR PLANTING" : "CERTIFICATE: UNVIABLE ENVIRONMENT", 105, yPos + 12, { align: "center" });

        doc.setFontSize(10);
        doc.setFont("helvetica", "normal");
        doc.setTextColor(60, 60, 60);
        const verdictText = isViable
            ? "Predicted Yield Days are within acceptable agricultural ranges for the selected genomic samples."
            : "Environmental conditions (Rainfall, Temp, or Soil) do not meet the minimum requirements for rice cultivation.";
        doc.text(verdictText, 105, yPos + 24, { align: "center" });

        yPos += 50;

        // 6. GENOMIC PREDICTIONS
        doc.setFontSize(14);
        doc.setFont("helvetica", "bold");
        doc.setTextColor(0, 0, 0);
        doc.text("Genomic Yield Predictions", 14, yPos);
        yPos += 5;

        const predData = results.map(r => [
            r.sample_id,
            r.confidence.includes("Unsuitable") ? "FAILED" : `${r.predicted_days} Days`,
            r.confidence.includes("Unsuitable")
                ? r.confidence.replace("Unsuitable Environment:", "").substring(0, 60)
                : r.confidence
        ]);

        autoTable(doc, {
            startY: yPos,
            head: [['Sample ID', 'Est. Maturity', 'Status / Failure Reason']],
            body: predData,
            theme: 'striped',
            headStyles: { fillColor: [51, 65, 85], halign: 'left' },
            styles: { fontSize: 9, cellPadding: 3 },
            margin: { left: 14, right: 14 }
        });

        const dateStr = now.toISOString().split('T')[0];
        const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '-');
        doc.save(`Agronomic_Analysis_${dateStr}_${timeStr}.pdf`);
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
                                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                                    <div className="flex items-center gap-2">
                                        <MapPin className="h-5 w-5 text-emerald-600" />
                                        <h2 className="text-lg font-semibold text-slate-800">Location Context</h2>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => setShowMap(!showMap)}
                                        className="text-sm flex items-center gap-1.5 text-emerald-600 hover:text-emerald-700 font-medium transition-colors"
                                    >
                                        {showMap ? <X className="w-4 h-4" /> : <MapIcon className="w-4 h-4" />}
                                        {showMap ? 'Close Map' : 'Select on Map'}
                                    </button>
                                </div>

                                {showMap && (
                                    <div id="map-capture" className="h-[400px] w-full rounded-xl overflow-hidden border border-slate-200 shadow-inner z-0 relative">
                                        <MapContainer
                                            center={getMapCenter()}
                                            zoom={5}
                                            style={{ height: '100%', width: '100%' }}
                                            className="z-0"
                                        >
                                            <MapController onRegister={(map) => { mapInstance.current = map; }} />
                                            <TileLayer
                                                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                                                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                                                crossOrigin="anonymous"
                                            />
                                            <LocationMarker
                                                position={
                                                    (latitude && longitude && !isNaN(parseFloat(latitude)) && !isNaN(parseFloat(longitude)))
                                                        ? { lat: parseFloat(latitude), lng: parseFloat(longitude) }
                                                        : null
                                                }
                                                setPosition={handleMapUpdate}
                                            />
                                        </MapContainer>
                                        <div className="absolute bottom-2 left-2 bg-white/90 backdrop-blur-sm px-3 py-1.5 rounded-lg text-xs font-medium text-slate-600 border border-slate-200/50 pointer-events-none z-[1000]">
                                            Click anywhere to set location
                                        </div>
                                    </div>
                                )}

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
                            <div className="flex items-center justify-between h-full pb-2">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 bg-emerald-100 rounded-lg">
                                        <BarChart3 className="h-6 w-6 text-emerald-700" />
                                    </div>
                                    <div>
                                        <h2 className="text-2xl font-bold text-slate-900">Analysis Results</h2>
                                        <p className="text-slate-600">Predictions based on your inputs</p>
                                    </div>
                                </div>
                                <button
                                    onClick={generatePDF}
                                    className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:text-emerald-700 hover:border-emerald-200 rounded-lg text-sm font-medium transition-all shadow-sm"
                                >
                                    <Download className="w-4 h-4" />
                                    Download Report
                                </button>
                            </div>
                        </div>

                        <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 overflow-hidden border border-slate-100 lg:h-[calc(100%-7rem)] flex flex-col">
                            <div className="lg:hidden p-6 border-b border-gray-100 bg-emerald-50/50 flex justify-between items-center">
                                <h2 className="text-xl font-bold text-slate-800">Analysis Results</h2>
                                <button
                                    onClick={generatePDF}
                                    className="p-2 text-slate-500 hover:text-emerald-600 transition-colors"
                                    title="Download Report"
                                >
                                    <Download className="w-5 h-5" />
                                </button>
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
