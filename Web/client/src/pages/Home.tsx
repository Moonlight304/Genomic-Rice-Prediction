import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ArrowRight, Leaf, Database, Activity, Cpu } from 'lucide-react';

const Home = () => {
    const { user } = useAuth();

    return (
        <div className="min-h-[calc(100vh-4rem)] flex flex-col">
            {/* Hero Section */}
            <div className="flex-1 bg-gradient-to-b from-white to-emerald-50/50">
                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 text-center">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-sm font-medium mb-8 animate-fade-in-up">
                        <span className="flex h-2 w-2 rounded-full bg-emerald-600"></span>
                        Advanced Genomic Analysis Platform
                    </div>
                    
                    <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 mb-6">
                        Analyze Rice Genomics with <br/>
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 to-teal-600">
                            Machine Learning
                        </span>
                    </h1>
                    
                    <p className="mt-4 max-w-2xl mx-auto text-xl text-slate-600 mb-10 leading-relaxed">
                        Leverage the power of advanced algorithms and environmental data to explore genetic traits and optimize agricultural research.
                    </p>

                    <div className="flex justify-center gap-4">
                        {user ? (
                            <Link
                                to="/predict"
                                className="inline-flex items-center px-8 py-3 text-lg font-medium text-white bg-emerald-600 rounded-full hover:bg-emerald-700 shadow-lg shadow-emerald-200 hover:shadow-xl transition-all hover:-translate-y-0.5"
                            >
                                Start Analysis
                                <ArrowRight className="ml-2 h-5 w-5" />
                            </Link>
                        ) : (
                            <Link
                                to="/register"
                                className="inline-flex items-center px-8 py-3 text-lg font-medium text-white bg-emerald-600 rounded-full hover:bg-emerald-700 shadow-lg shadow-emerald-200 hover:shadow-xl transition-all hover:-translate-y-0.5"
                            >
                                Get Started Free
                                <ArrowRight className="ml-2 h-5 w-5" />
                            </Link>
                        )}
                        <a 
                            href="#features"
                            className="inline-flex items-center px-8 py-3 text-lg font-medium text-slate-700 bg-white border border-slate-200 rounded-full hover:bg-slate-50 hover:border-slate-300 transition-all"
                        >
                            Learn More
                        </a>
                    </div>
                </main>
            </div>

            {/* Features Grid */}
            <div id="features" className="bg-white py-24 border-t border-emerald-100">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl font-bold text-slate-900 mb-4">Why Choose AgriGenomics?</h2>
                        <p className="text-slate-600 max-w-2xl mx-auto">Our platform combines cutting-edge technology with environmental science to deliver accurate insights.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                        {[
                            {
                                icon: <Cpu className="h-6 w-6 text-emerald-600" />,
                                title: "Advanced ML Models",
                                desc: "Utilizing state-of-the-art algorithms trained on vast genomic datasets."
                            },
                            {
                                icon: <Leaf className="h-6 w-6 text-emerald-600" />,
                                title: "Environmental Context",
                                desc: "Integration with real-time soil and weather data for precise localization."
                            },
                            {
                                icon: <Database className="h-6 w-6 text-emerald-600" />,
                                title: "Secure Data Storage",
                                desc: "Your research data is encrypted and safely stored for future reference."
                            },
                            {
                                icon: <Activity className="h-6 w-6 text-emerald-600" />,
                                title: "Real-time Processing",
                                desc: "Get instant insights and detailed analytics for your genomic samples."
                            }
                        ].map((feature, idx) => (
                            <div key={idx} className="p-6 bg-slate-50 rounded-2xl border border-slate-100 hover:border-emerald-200 hover:shadow-lg transition-all">
                                <div className="w-12 h-12 bg-white rounded-xl shadow-sm flex items-center justify-center mb-4 border border-slate-100">
                                    {feature.icon}
                                </div>
                                <h3 className="text-lg font-semibold text-slate-900 mb-2">{feature.title}</h3>
                                <p className="text-slate-600">{feature.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Home;
