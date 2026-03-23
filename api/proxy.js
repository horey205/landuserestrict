export default async function handler(req, res) {
    const { url } = req.query;
    if (!url) return res.status(400).send("No URL provided");
    
    try {
        const decodedUrl = decodeURIComponent(url);
        const response = await fetch(decodedUrl);
        const data = await response.arrayBuffer(); // Use arrayBuffer for images/binary
        
        // Forward headers
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Content-Type', response.headers.get('Content-Type') || 'application/octet-stream');
        
        res.status(200).send(Buffer.from(data));
    } catch (e) {
        res.status(500).send(e.toString());
    }
}
