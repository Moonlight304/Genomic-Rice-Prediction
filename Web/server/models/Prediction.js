const mongoose = require('mongoose');

const PredictionSchema = new mongoose.Schema({
    user: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },

    sample_name: {
        type: String,
        required: true
    },
    timestamp: {
        type: Date,
        default: Date.now
    },

    location: {
        lat: Number,
        lon: Number
    },
    environmental_data: {
        rainfall: Number,
        temp: Number,
        soil_ph: Number,
        soil_nitrogen: Number
    },

    results: [
        {
            sample_id: String,
            predicted_days: Number,
            confidence: String
        }
    ]
});

module.exports = mongoose.model('Prediction', PredictionSchema);