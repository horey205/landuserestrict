export default async function handler(req, res) {
    let { url, ...params } = req.query;
    if (!url) return res.status(400).send("No URL provided");
    
    try {
        const decodedUrl = decodeURIComponent(url);
        // Reconstruct full VWorld URL with all query params (for WMS tile requests)
        const queryStr = new URLSearchParams(params).toString();
        const fullUrl = queryStr ? `${decodedUrl}${decodedUrl.includes('?') ? '&' : '?'}${queryStr}` : decodedUrl;
        
        const response = await fetch(fullUrl);
        const data = await response.arrayBuffer();
        
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Content-Type', response.headers.get('Content-Type') || 'application/octet-stream');
        res.status(200).send(Buffer.from(data));
    } catch (e) {
        res.status(500).send(e.toString());
    }
}
