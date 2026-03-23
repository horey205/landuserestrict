const https = require('https');

export default function handler(req, res) {
    let { url, ...params } = req.query;
    if (!url) return res.status(400).send("No URL provided");
    
    try {
        const decodedUrl = decodeURIComponent(url);
        // Reconstruct full URL with all query parameters (for WMS/WFS/Data API)
        const queryStr = new URLSearchParams(params).toString();
        const fullUrl = queryStr ? `${decodedUrl}${decodedUrl.includes('?') ? '&' : '?'}${queryStr}` : decodedUrl;
        
        // Use native Node.js https module for maximum compatibility with government API firewalls
        https.get(fullUrl, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': req.headers.referer || 'https://vworld.kr'
            },
            timeout: 10000 // 10s timeout
        }, (vRes) => {
            // Forward VWorld's response directly to the browser
            res.setHeader('Access-Control-Allow-Origin', '*');
            res.setHeader('Content-Type', vRes.headers['content-type'] || 'application/octet-stream');
            vRes.pipe(res);
        }).on('error', (e) => {
            console.error("VWorld Proxy Error:", e.message);
            res.status(500).send("Proxying failed: " + e.message);
        });
    } catch (e) {
        res.status(500).send("Invalid proxy URL");
    }
}
