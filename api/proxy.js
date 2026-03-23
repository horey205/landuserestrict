export default async function handler(req, res) {
    let { url, ...params } = req.query;
    if (!url) return res.status(400).send("No URL provided");
    
    try {
        const decodedUrl = decodeURIComponent(url);
        const queryStr = new URLSearchParams(params).toString();
        const fullUrl = queryStr ? `${decodedUrl}${decodedUrl.includes('?') ? '&' : '?'}${queryStr}` : decodedUrl;
        
        // Use browser's headers to pass VWorld authentication checks
        const response = await fetch(fullUrl, {
            headers: {
                'Referer': req.headers.referer || '',
                'User-Agent': req.headers['user-agent'] || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        });
        
        const data = await response.arrayBuffer();
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Content-Type', response.headers.get('Content-Type') || 'application/octet-stream');
        res.status(200).send(Buffer.from(data));
    } catch (e) {
        console.error("Proxy Error:", e);
        res.status(500).send(e.toString());
    }
}
