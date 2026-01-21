const express = require("express");
const multer = require("multer");
const axios = require("axios");
const dotenv = require('dotenv').config();
const FormData = require("form-data");
const fs = require("fs");
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const cookieParser = require('cookie-parser');
const User = require('./models/User');
const Prediction = require('./models/Prediction');
const { getEnvironmentalData } = require("./fetchEnv");
const authMiddleware = require('./middleware/authMiddleware');

const app = express();
const upload = multer({ dest: "uploads/" });

// --- MIDDLEWARE ---
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

        res.json({
            accessToken,
            user: { id: user._id, name: user.name }
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


// CORE PREDICTION ROUTE

app.post("/predict", authMiddleware, upload.single("file"), async (req, res) => {
    if (!req.file) return res.status(400).json({ error: "No file uploaded" });

    const lat = req.body.latitude;
    const lon = req.body.longitude;

    try {
        console.log(`[Node] Processing Request for Loc: ${lat}, ${lon}`);

        // 1. Fetch Environment (Weather + Calculated Fallbacks)
        const envData = await getEnvironmentalData(lat, lon);
        console.log("[Node] Env Data Ready.");

        // 2. Prepare Payload for Python
        const form = new FormData();
        form.append("file", fs.createReadStream(req.file.path), req.file.originalname);
        form.append("env_data", JSON.stringify(envData));

        if (lat) form.append("latitude", lat.toString());
        if (lon) form.append("longitude", lon.toString());

        // 3. Call Python Engine
        console.log("[Node] Forwarding to Python Engine...");
        const response = await axios.post(
            "http://localhost:8000/predict",
            form,
            { headers: form.getHeaders() }
        );

        try {
            // The python response is an array of predictions. 
            // For history, we grab the first sample's result as a summary.
            // const primaryResult = response.data[0];

            const newPrediction = {
                user: req.user.id,
                sample_name: req.file.originalname,
                location: { lat, lon },
                environmental_data: {
                    rainfall: envData.E_total_rain_mm,
                    temp: envData.E_avg_temp,
                    soil_ph: envData.E_soil_ph,
                    soil_nitrogen: envData.E_soil_nitrogen
                },
                results: response.data
            }

            console.log(newPrediction);
            await Prediction.create(newPrediction);

            console.log(`History Saved for User: ${req.user.id}`);
        }
        catch (saveErr) {
            console.error("History Save Failed:", saveErr.message);
        }

        fs.unlinkSync(req.file.path);
        res.json(response.data);

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

app.get('/health', (req, res) => {
    res.json({ "status": "ok" });
});

app.listen(5000, () => {
    console.log("Node gateway running on port 5000");
});