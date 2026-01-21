// fetchEnv.js
const axios = require('axios');
const http = require('http');
const https = require('https');

// --- 1. CONFIGURATION ---
// Force IPv4 to fix Node connection issues (ETIMEDOUT fix)
const httpAgent = new http.Agent({ family: 4 });
const httpsAgent = new https.Agent({ family: 4 });

// In-Memory Cache to store weather results for 10 minutes
// Prevents "Too Many Requests" errors and makes the demo instant.
const weatherCache = new Map();

// --- 2. HELPERS ---
const mean = (arr) => arr && arr.length > 0 ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
const sum = (arr) => arr && arr.length > 0 ? arr.reduce((a, b) => a + b, 0) : 0;

async function getEnvironmentalData(lat, lon) {
    // Default to India (Rice Belt) if coords are missing
    const validLat = lat || 20.59;
    const validLon = lon || 78.96;

    // --- 3. CACHE CHECK (Speed Optimization) ---
    // Create a unique key for this location (rounded to 2 decimals)
    const cacheKey = `${parseFloat(validLat).toFixed(2)}_${parseFloat(validLon).toFixed(2)}`;
    
    // If we have data less than 10 minutes old, return it instantly!
    if (weatherCache.has(cacheKey)) {
        const cached = weatherCache.get(cacheKey);
        const age = Date.now() - cached.timestamp;
        
        // 10 minutes = 600,000 ms
        if (age < 600000) { 
            console.log(`⚡ [GeoAPI] Serving Cached Data for ${cacheKey} (Instant)`);
            return cached.data;
        }
    }

    console.log(`[GeoAPI] Fetching Fresh Weather for: ${validLat}, ${validLon}...`);

    // Default Fallbacks (used if API completely fails)
    let result = {
        E_avg_temp: 28.5, E_max_temp: 34.2, E_total_rain_mm: 1200, 
        E_solar_radiation: 18.5, E_humidity_perc: 82.0, E_soil_moisture: 0.35,
        E_soil_ph: 6.5,      // Python will overwrite this with Real Map data
        E_soil_nitrogen: 2.1,// Calculated below
        E_co2_ppm: 421.0, E_o2_perc: 20.95
    };

    try {
        // --- 4. FETCH WEATHER (Open-Meteo) ---
        // Using "Last 30 Days" for speed and reliability
        const weatherUrl = `https://archive-api.open-meteo.com/v1/archive`;
        
        const weatherRes = await axios.get(weatherUrl, { 
            params: {
                latitude: validLat,
                longitude: validLon,
                start_date: '2023-11-01', // Static recent month for consistent demo results
                end_date: '2023-11-30',
                daily: 'temperature_2m_max,temperature_2m_mean,rain_sum,shortwave_radiation_sum',
                hourly: 'relative_humidity_2m,soil_moisture_0_to_7cm'
            },
            timeout: 10000, // 10s timeout
            httpAgent, 
            httpsAgent
        });

        const w = weatherRes.data;

        // --- 5. PARSE WEATHER ---
        result.E_avg_temp = parseFloat(mean(w.daily.temperature_2m_mean).toFixed(2));
        result.E_max_temp = parseFloat(Math.max(...w.daily.temperature_2m_max).toFixed(2));
        
        // Estimate Annual Rain (Monthly * 12)
        const monthly_rain = sum(w.daily.rain_sum);
        result.E_total_rain_mm = parseFloat((monthly_rain * 12).toFixed(2));
        
        result.E_solar_radiation = parseFloat(mean(w.daily.shortwave_radiation_sum).toFixed(2));
        result.E_humidity_perc = parseFloat(mean(w.hourly.relative_humidity_2m).toFixed(2));
        result.E_soil_moisture = parseFloat(mean(w.hourly.soil_moisture_0_to_7cm).toFixed(2));

        // --- 6. CALCULATE SOIL PROXIES (Smart Fallbacks) ---
        
        // A. pH Algorithm (Python will likely overwrite this with the 1.7GB file)
        // More Rain = More Acidic (Lower pH)
        let estimated_ph = 7.5 - (result.E_total_rain_mm / 2000);
        result.E_soil_ph = parseFloat(Math.min(Math.max(estimated_ph, 4.5), 8.5).toFixed(2));

        // B. Nitrogen Algorithm (Biogeochemical Proxy)
        // Replaces simple formula with Temperature + Moisture logic
        // Logic: Microbes need both Water and Heat (20-35°C) to make Nitrogen available.
        
        // Base Nitrogen from Moisture (Vegetation support)
        let n_base = 0.5 + (result.E_soil_moisture * 4.0);
        
        // Temperature Modifier
        let temp_factor = 1.0;
        if (result.E_avg_temp > 20 && result.E_avg_temp < 35) {
            temp_factor = 1.2; // Optimal decomposition heat
        }
        else {
            temp_factor = 0.8; // Too cold or too hot slows microbes
        }

        let estimated_n = n_base * temp_factor;
        
        // Clamp to realistic limits (0.5 to 4.0 g/kg)
        result.E_soil_nitrogen = parseFloat(Math.min(Math.max(estimated_n, 0.5), 4.0).toFixed(2));

        console.log(`[GeoAPI] Weather Ready. Calc pH: ${result.E_soil_ph}, Smart Calc N: ${result.E_soil_nitrogen}`);

        // --- 7. SAVE TO CACHE ---
        weatherCache.set(cacheKey, {
            timestamp: Date.now(),
            data: result
        });

    }
    catch (error) {
        console.error("[GeoAPI] Weather API Failed:", error.message);
    }

    return result;
}

module.exports = { getEnvironmentalData };