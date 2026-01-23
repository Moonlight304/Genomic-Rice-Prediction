import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Sprout, LogOut, User as UserIcon, Settings, ChevronDown } from 'lucide-react';

const Navbar: React.FC = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsDropdownOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const isActive = (path: string) => {
        return location.pathname === path
            ? "text-emerald-700 bg-emerald-50 font-semibold"
            : "text-gray-600 hover:text-emerald-600 hover:bg-slate-50";
    };

    return (
        <nav className="bg-white border-b border-gray-100 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex items-center">
                        <Link to="/" className="flex items-center gap-2">
                            <div className="bg-emerald-600 p-2 rounded-lg">
                                <Sprout className="h-6 w-6 text-white" />
                            </div>
                            <span className="text-xl font-bold bg-gradient-to-r from-emerald-800 to-emerald-600 bg-clip-text text-transparent">
                                AgriGenomics
                            </span>
                        </Link>
                    </div>

                    <div className="flex items-center gap-4">
                        {user ? (
                            <div className="flex items-center gap-4">
                                <Link to="/predict" className={`${isActive('/predict')} px-3 py-2 rounded-md text-sm transition-colors`}>
                                    Analysis
                                </Link>
                                <Link to="/history" className={`${isActive('/history')} px-3 py-2 rounded-md text-sm transition-colors`}>
                                    History
                                </Link>
                                <div className="h-6 w-px bg-gray-200 mx-2"></div>
                                
                                <div className="relative" ref={dropdownRef}>
                                    <button 
                                        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                                        className="flex items-center gap-2 text-gray-700 hover:text-emerald-700 bg-slate-50 hover:bg-emerald-50 px-3 py-1.5 rounded-full border border-slate-100 transition-colors"
                                    >
                                        <UserIcon className="h-4 w-4 text-emerald-600" />
                                        <span className="text-sm font-medium">{user.name}</span>
                                        <ChevronDown className={`h-3 w-3 text-gray-400 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
                                    </button>

                                    {isDropdownOpen && (
                                        <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-slate-100 py-1 animate-fade-in-down origin-top-right">
                                            <Link 
                                                to="/profile" 
                                                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-slate-50 hover:text-emerald-600"
                                                onClick={() => setIsDropdownOpen(false)}
                                            >
                                                <Settings className="h-4 w-4" />
                                                Settings
                                            </Link>
                                            <div className="h-px bg-slate-100 my-1"></div>
                                            <button
                                                onClick={() => {
                                                    handleLogout();
                                                    setIsDropdownOpen(false);
                                                }}
                                                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 text-left"
                                            >
                                                <LogOut className="h-4 w-4" />
                                                Sign Out
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="flex items-center gap-3">
                                <Link
                                    to="/login"
                                    className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                                >
                                    Sign In
                                </Link>
                                <Link
                                    to="/register"
                                    className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm shadow-emerald-200 transition-all hover:shadow-md"
                                >
                                    Get Started
                                </Link>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
