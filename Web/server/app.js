const express = require("express");
const multer = require("multer");
const axios = require("axios");
const FormData = require("form-data");
const fs = require("fs");
const { getEnvironmentalData } = require("./fetchEnv");

const app = express();
const upload = multer({ dest: "uploads/" });

app.get('/health', (req, res) => {
    res.json({ "status": "ok" });
});

app.post("/predict", upload.single("file"), async (req, res) => {
    if (!req.file) return res.status(400).json({ error: "No file uploaded" });

    // 1. Get Coords
    const lat = req.body.latitude;
    const lon = req.body.longitude;

    try {
        console.log(`[Node] Processing Request for Loc: ${lat}, ${lon}`);

        // 2. Fetch Data (Node handles Weather + Fallbacks)
        const envData = await getEnvironmentalData(lat, lon);
        console.log("[Node] Env Data Ready.");

        // 3. Prepare Form for Python
        const form = new FormData();
        form.append("file", fs.createReadStream(req.file.path), req.file.originalname);
        form.append("env_data", JSON.stringify(envData));

        // --- NEW: Forward Coordinates to Python for Soil Lookup ---
        if (lat) form.append("latitude", lat.toString());
        if (lon) form.append("longitude", lon.toString());

        // 4. Send to FastAPI
        console.log("[Node] Forwarding to Python Engine...");
        const response = await axios.post(
            "http://localhost:8000/predict",
            form,
            { headers: form.getHeaders() }
        );

        fs.unlinkSync(req.file.path); 
        res.json(response.data);

    } catch (err) {
        console.error("[Node] Error:", err.message);
        if (req.file && fs.existsSync(req.file.path)) fs.unlinkSync(req.file.path);
        
        res.status(500).json({
            error: "Prediction failed",
            details: err.response?.data || err.message
        });
    }
});

app.listen(5000, () => {
    console.log("Node gateway running on port 5000");
});