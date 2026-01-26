const express = require("express");
const multer = require("multer");
const cors = require("cors");
const axios = require("axios");
const dotenv = require('dotenv').config();
const FormData = require("form-data");
const fs = require("fs");
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cookieParser = require('cookie-parser');
const nodemailer = require('nodemailer');
const crypto = require('crypto');
const User = require('./models/User');
const Prediction = require('./models/Prediction');
const { getEnvironmentalData } = require("./fetchEnv");
const authMiddleware = require('./middleware/authMiddleware');

const app = express();
const upload = multer({ dest: "uploads/" });

// --- MIDDLEWARE ---
app.use(cors({
    origin: [process.env.CLIENT_URL],
    credentials: true
}));
app.use(express.json());
app.use(cookieParser());

// --- DB CONNECTION ---
mongoose.connect(process.env.MONGO_URI)
    .then(() => console.log('DB Connected'))
    .catch((e) => console.log('DB Error:', e.message));

// --- SECRETS ---
const ACCESS_TOKEN_SECRET = process.env.ACCESS_SECRET;
const REFRESH_TOKEN_SECRET = process.env.REFRESH_SECRET;

// AUTH ROUTES

// 1. REGISTER
app.post('/register', async (req, res) => {
    const { name, email, password } = req.body;

    try {
        const salt = await bcrypt.genSalt(10);
        const hashedPassword = await bcrypt.hash(password, salt);

        await User.create({ name, email, password: hashedPassword });

        console.log("New Use Registered!");
        console.log({ email, name });
        
        res.json({ message: "User created successfully" });
    }
    catch (err) {
        res.status(400).json({ error: "Email already exists" });
    }
});

// 2. LOGIN
app.post('/login', async (req, res) => {
    const { email, password } = req.body;

    try {
        const user = await User.findOne({ email });
        if (!user) return res.status(400).json({ error: "User not found" });

        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) return res.status(400).json({ error: "Invalid credentials" });

        const accessToken = jwt.sign({ id: user._id }, ACCESS_TOKEN_SECRET, { expiresIn: '15m' });

        const refreshToken = jwt.sign({ id: user._id }, REFRESH_TOKEN_SECRET, { expiresIn: '14d' });

        // C. Set Cookie (The Secure Part)
        res.cookie('refreshToken', refreshToken, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: process.env.NODE_ENV === 'production' ? 'None' : 'Lax',
            path: '/',
            maxAge: 14 * 24 * 60 * 60 * 1000
        });

        console.log("New Use Login!");
        console.log({ email: user.email, username: user.name });

        res.json({
            accessToken,
            user: { id: user._id, name: user.name, email: user.email }
        });

    }
    catch (err) {
        res.status(500).json({ error: "Server error" });
    }
});

// 3. REFRESH (Get new Access Token using Cookie)
app.post('/refresh', (req, res) => {
    const refreshToken = req.cookies.refreshToken;

    if (!refreshToken) return res.status(401).json({ error: "No Refresh Token" });

    jwt.verify(refreshToken, REFRESH_TOKEN_SECRET, (err, user) => {
        if (err)
            return res.status(403).json({ error: "Invalid Refresh Token" });

        // Issue new Access Token
        const newAccessToken = jwt.sign({ id: user.id }, ACCESS_TOKEN_SECRET, { expiresIn: '15m' });

        res.json({ accessToken: newAccessToken });
    });
});

// 4. LOGOUT
app.post('/logout', (req, res) => {
    res.clearCookie('refreshToken');
    res.json({ message: "Logged out" });
});

// 5. GET HISTORY
app.get('/history', authMiddleware, async (req, res) => {
    if (!req.user) return res.status(401).json({ error: "Unauthorized" });

    try {
        const history = await Prediction.find({ user: req.user.id })
            .sort({ timestamp: -1 })

        res.json(history);
    }
    catch (err) {
        res.status(500).json({ error: "Could not fetch history" });
    }
});

// 6. UPDATE PROFILE
app.put('/profile/update', authMiddleware, async (req, res) => {
    if (!req.user) return res.status(401).json({ error: "Unauthorized" });
    const { name } = req.body;
    try {
        const user = await User.findByIdAndUpdate(req.user.id, { name }, { new: true });
        res.json({ user: { id: user._id, name: user.name } });
    } catch (err) {
        res.status(500).json({ error: "Could not update profile" });
    }
});

// 7. CHANGE PASSWORD
app.put('/profile/password', authMiddleware, async (req, res) => {
    if (!req.user) return res.status(401).json({ error: "Unauthorized" });
    const { currentPassword, newPassword } = req.body;
    try {
        const user = await User.findById(req.user.id);
        const isMatch = await bcrypt.compare(currentPassword, user.password);
        if (!isMatch) return res.status(400).json({ error: "Incorrect current password" });

        const salt = await bcrypt.genSalt(10);
        user.password = await bcrypt.hash(newPassword, salt);
        await user.save();
        
        res.json({ message: "Password updated successfully" });
    } catch (err) {
        res.status(500).json({ error: "Could not change password" });
    }
});

// 8. DELETE ACCOUNT
app.delete('/profile', authMiddleware, async (req, res) => {
    if (!req.user) return res.status(401).json({ error: "Unauthorized" });
    try {
        await Prediction.deleteMany({ user: req.user.id });
        await User.findByIdAndDelete(req.user.id);
        
        res.clearCookie('refreshToken');
        res.json({ message: "Account deleted successfully" });
    } catch (err) {
        res.status(500).json({ error: "Could not delete account" });
    }
});

// 9. FORGOT PASSWORD
const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS
    }
});

app.post('/forgot-password', async (req, res) => {
    const { email } = req.body;
    try {
        const user = await User.findOne({ email });
        if (!user) return res.status(404).json({ error: "User not found" });

        const token = crypto.randomBytes(20).toString('hex');
        user.resetPasswordToken = token;
        user.resetPasswordExpires = Date.now() + 3600000; // 1 hour
        await user.save();

        const resetLink = `${process.env.CLIENT_URL || 'http://localhost:5173'}/reset-password/${token}`;

        const htmlContent = `
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; padding: 40px 0;">
            <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); overflow: hidden; border: 1px solid #e2e8f0;">
                <div style="background: linear-gradient(135deg, #059669 0%, #047857 100%); padding: 30px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.5px;">AgriGenomics</h1>
                </div>
                <div style="padding: 40px 30px;">
                    <h2 style="color: #1e293b; margin-top: 0; margin-bottom: 20px; font-size: 20px; font-weight: 600;">Reset Your Password</h2>
                    <p style="color: #475569; font-size: 16px; line-height: 1.6; margin-bottom: 24px;">
                        Hello, we received a request to reset the password for your account. If you didn't make this request, you can safely ignore this email.
                    </p>
                    <div style="text-align: center; margin: 32px 0;">
                        <a href="${resetLink}" style="background-color: #059669; color: #ffffff; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 16px; display: inline-block; box-shadow: 0 4px 6px -1px rgba(5, 150, 105, 0.2);">
                            Reset Password
                        </a>
                    </div>
                    <p style="color: #64748b; font-size: 14px; line-height: 1.5; margin-top: 32px; border-top: 1px solid #f1f5f9; padding-top: 20px;">
                        If the button doesn't work, copy and paste this link into your browser:<br>
                        <a href="${resetLink}" style="color: #059669; text-decoration: none; word-break: break-all;">${resetLink}</a>
                    </p>
                </div>
                <div style="background-color: #f8fafc; padding: 20px; text-align: center; color: #94a3b8; font-size: 12px; border-top: 1px solid #e2e8f0;">
                    &copy; ${new Date().getFullYear()} AgriGenomics Project. All rights reserved.
                </div>
            </div>
        </div>
        `;

        const mailOptions = {
            from: `"AgriGenomics Security" <${process.env.EMAIL_USER}>`,
            to: user.email,
            subject: 'Reset your AgriGenomics Password',
            text: `Reset your password here: ${resetLink}`,
            html: htmlContent
        };

        console.log(`Reset Link for ${email}: ${resetLink}`);

        transporter.sendMail(mailOptions, (err) => {
            if (err) {
                console.log("\n---------------------------------------------------");
                console.log("NOTE: Email delivery failed. (Expected in Dev Mode)");
                console.log("Reason: " + err.message.split('\n')[0]);
                console.log(">> USE THIS LINK TO RESET PASSWORD: <<");
                console.log(resetLink);
                console.log("---------------------------------------------------\n");
                
                return res.json({ message: "Development: Check server logs for link" });
            }
            res.json({ message: "Password reset email sent" });
        });

    } catch (err) {
        res.status(500).json({ error: "Server error" });
    }
});

// 10. RESET PASSWORD
app.post('/reset-password/:token', async (req, res) => {
    try {
        const user = await User.findOne({ 
            resetPasswordToken: req.params.token, 
            resetPasswordExpires: { $gt: Date.now() } 
        });

        if (!user) return res.status(400).json({ error: "Password reset token is invalid or has expired" });

        const { password } = req.body;
        if (password) {
            const salt = await bcrypt.genSalt(10);
            user.password = await bcrypt.hash(password, salt);
            user.resetPasswordToken = undefined;
            user.resetPasswordExpires = undefined;
            await user.save();
            res.json({ message: "Password updated successfully" });
        } else {
             res.status(400).json({ error: "Password is required" });
        }
    } catch (err) {
         res.status(500).json({ error: "Server error" });
    }
});

// CORE PREDICTION ROUTE
app.post("/predict", authMiddleware, upload.single("file"), async (req, res) => {
    if (!req.file) return res.status(400).json({ error: "No file uploaded" });

    const lat = req.body.latitude;
    const lon = req.body.longitude;
    const month = parseInt(req.body.month) || 7;
    const irrigation = req.body.irrigation === 'true';

    try {
        console.log(`[Node] Processing Request for Loc: ${lat}, ${lon}, Month: ${month}, Irrig: ${irrigation}`);

        // --- 1. FETCH ENVIRONMENT ---
        const envData = await getEnvironmentalData(lat, lon, month, irrigation);
        console.log("[Node] Env Data Ready.");

        // --- 2. PREPARE PAYLOAD ---
        const form = new FormData();
        form.append("file", fs.createReadStream(req.file.path), req.file.originalname);
        form.append("env_data", JSON.stringify(envData));

        if (lat) form.append("latitude", lat.toString());
        if (lon) form.append("longitude", lon.toString());

        // --- 3. CALL PYTHON ENGINE ---
        console.log("[Node] Forwarding to Python Engine...");
        const response = await axios.post(
            `${process.env.fastAPI_URL}/predict`,
            form,
            { headers: form.getHeaders() }
        );

        try {
            const newPrediction = {
                user: req.user.id,
                sample_name: req.file.originalname,
                location: { lat, lon },
                month: month,
                irrigation: irrigation,
                environmental_data: {
                    rainfall: envData.E_total_rain_mm,
                    temp: envData.E_avg_temp,
                    soil_ph: envData.E_soil_ph,
                    soil_nitrogen: envData.E_soil_nitrogen,
                    solar_radiation: envData.E_solar_radiation
                },
                results: response.data
            }

            console.log(newPrediction);
            const savedPrediction = await Prediction.create(newPrediction);
            
            await User.findByIdAndUpdate(req.user.id, { 
                $push: { predictions: savedPrediction._id } 
            });

            console.log(`History Saved for User: ${req.user.id}`);
        }
        catch (saveErr) {
            console.error("History Save Failed:", saveErr.message);
        }

        fs.unlinkSync(req.file.path);
        
        res.json({
            predictions: response.data,
            environmental_data: envData
        });

    }
    catch (err) {
        console.error("[Node] Error:", err.message);
        if (req.file && fs.existsSync(req.file.path)) fs.unlinkSync(req.file.path);

        res.status(500).json({
            error: "Prediction failed",
            details: err.response?.data || err.message
        });
    }
});

app.get('/health', (req, res) => {
    res.json({ "status": "ok" });
});

app.listen(5000, () => {
    console.log("Node gateway running on port 5000");
});