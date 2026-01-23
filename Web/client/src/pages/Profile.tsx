import React, { useState } from 'react';
import API from '../api/axios';
import { useAuth } from '../context/AuthContext';
import { User, Lock, Trash2, AlertTriangle, Check, Save } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Profile = () => {
    const { user, updateUser, logout } = useAuth();
    const navigate = useNavigate();

    // Name State
    const [name, setName] = useState(user?.name || '');
    const [nameStatus, setNameStatus] = useState<null | 'success' | 'error'>(null);
    const [isUpdatingName, setIsUpdatingName] = useState(false);
    const [currPassword, setCurrPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [passStatus, setPassStatus] = useState<null | 'success' | 'error'>(null);
    const [passMessage, setPassMessage] = useState('');
    const [isUpdatingPass, setIsUpdatingPass] = useState(false);

    // Delete State
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const handleUpdateName = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsUpdatingName(true);
        try {
            const res = await API.put('/profile/update', { name });
            updateUser({ ...user!, name: res.data.user.name });
            setNameStatus('success');
            setTimeout(() => setNameStatus(null), 3000);
        } catch (err) {
            setNameStatus('error');
        } finally {
            setIsUpdatingName(false);
        }
    };

    const handleChangePassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setPassStatus(null);
        if (newPassword !== confirmPassword) {
            setPassStatus('error');
            setPassMessage("New passwords don't match");
            return;
        }
        if (newPassword.length < 6) {
            setPassStatus('error');
            setPassMessage("Password must be at least 6 characters");
            return;
        }

        setIsUpdatingPass(true);
        try {
            await API.put('/profile/password', {
                currentPassword: currPassword,
                newPassword
            });
            setPassStatus('success');
            setPassMessage("Password updated successfully");
            setCurrPassword('');
            setNewPassword('');
            setConfirmPassword('');
            setTimeout(() => setPassStatus(null), 3000);
        } catch (err) {
            setPassStatus('error');
            setPassMessage("Incorrect current password");
        } finally {
            setIsUpdatingPass(false);
        }
    };

    const handleDeleteAccount = async () => {
        setIsDeleting(true);
        try {
            await API.delete('/profile');
            await logout();
            navigate('/login');
        } catch (err) {
            console.error("Failed to delete account");
            setIsDeleting(false);
        }
    };

    return (
        <div className="min-h-[calc(100vh-4rem)] bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto space-y-8">

                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold text-slate-900">Account Settings</h1>
                    <p className="mt-2 text-slate-600">Manage your profile information and security.</p>
                </div>

                {/* Profile Information */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                    <div className="p-6 border-b border-slate-100 bg-slate-50/50">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-emerald-100 rounded-lg">
                                <User className="h-5 w-5 text-emerald-600" />
                            </div>
                            <h2 className="text-lg font-semibold text-slate-900">Profile Information</h2>
                        </div>
                    </div>

                    <div className="p-6">
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                                Email Address
                            </label>
                            <input
                                type="email"
                                value={user?.email || ''}
                                disabled
                                className="w-full px-4 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-500 cursor-not-allowed select-none"
                            />
                            <p className="mt-1 text-xs text-slate-400">Email address cannot be changed</p>
                        </div>

                        <form onSubmit={handleUpdateName} className="flex gap-4 items-end">
                            <div className="flex-1">
                                <label className="block text-sm font-medium text-slate-700 mb-1">
                                    Display Name
                                </label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
                                    placeholder="Enter your name"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={isUpdatingName || name === user?.name}
                                className="px-6 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                            >
                                {isUpdatingName ? (
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                ) : nameStatus === 'success' ? (
                                    <Check className="h-5 w-5" />
                                ) : (
                                    <Save className="h-5 w-5" />
                                )}
                                {nameStatus === 'success' ? 'Saved' : 'Save'}
                            </button>
                        </form>
                    </div>
                </div>

                {/* Security */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                    <div className="p-6 border-b border-slate-100 bg-slate-50/50">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-blue-100 rounded-lg">
                                <Lock className="h-5 w-5 text-blue-600" />
                            </div>
                            <h2 className="text-lg font-semibold text-slate-900">Change Password</h2>
                        </div>
                    </div>
                    <div className="p-6">
                        <form onSubmit={handleChangePassword} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">
                                    Current Password
                                </label>
                                <input
                                    type="password"
                                    value={currPassword}
                                    onChange={(e) => setCurrPassword(e.target.value)}
                                    className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
                                />
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">
                                        New Password
                                    </label>
                                    <input
                                        type="password"
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                        className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">
                                        Confirm New Password
                                    </label>
                                    <input
                                        type="password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className="w-full px-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
                                    />
                                </div>
                            </div>

                            {passMessage && (
                                <div className={`text-sm ${passStatus === 'error' ? 'text-red-600' : 'text-emerald-600'}`}>
                                    {passMessage}
                                </div>
                            )}

                            <div className="flex justify-end">
                                <button
                                    type="submit"
                                    disabled={isUpdatingPass || !currPassword || !newPassword}
                                    className="px-6 py-2 bg-slate-900 text-white rounded-lg font-medium hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    {isUpdatingPass ? 'Updating...' : 'Update Password'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>

                {/* Danger Zone */}
                <div className="bg-red-50 rounded-xl shadow-sm border border-red-100 overflow-hidden">
                    <div className="p-6">
                        <div className="flex items-start gap-4">
                            <div className="p-3 bg-red-100 rounded-lg shrink-0">
                                <AlertTriangle className="h-6 w-6 text-red-600" />
                            </div>
                            <div className="flex-1">
                                <h2 className="text-lg font-semibold text-red-900">Delete Account</h2>
                                <p className="mt-1 text-sm text-red-700">
                                    Permanently remove your account and all associated data. This action cannot be undone.
                                </p>
                            </div>
                            <button
                                onClick={() => setShowDeleteConfirm(true)}
                                className="px-4 py-2 bg-white border border-red-200 text-red-600 rounded-lg font-medium hover:bg-red-50 hover:border-red-300 transition-colors shadow-sm"
                            >
                                Delete Account
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Delete Confirmation Modal */}
            {showDeleteConfirm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
                    <div className="bg-white rounded-2xl shadow-xl max-w-md w-full overflow-hidden p-6 space-y-6">
                        <div className="flex flex-col items-center text-center">
                            <div className="p-4 bg-red-100 rounded-full mb-4">
                                <Trash2 className="h-8 w-8 text-red-600" />
                            </div>
                            <h3 className="text-xl font-bold text-slate-900">Delete your account?</h3>
                            <p className="mt-2 text-slate-600">
                                Are you sure you want to delete your account? All of your predictions and history will be permanently removed.
                            </p>
                        </div>
                        <div className="flex gap-4">
                            <button
                                onClick={() => setShowDeleteConfirm(false)}
                                className="flex-1 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg font-medium hover:bg-slate-50 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleDeleteAccount}
                                disabled={isDeleting}
                                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
                            >
                                {isDeleting ? 'Deleting...' : 'Yes, Delete'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Profile;
