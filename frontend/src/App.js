import React, { useState } from 'react';
import {
  Container,
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Grid,
  CircularProgress,
  Alert,
  Snackbar,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import SendIcon from '@mui/icons-material/Send';

const Input = styled('input')({
  display: 'none',
});

const App = () => {
  const [simplifiedText, setSimplifiedText] = useState('');
  const [originalText, setOriginalText] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [error, setError] = useState('');
  const [openSnackbar, setOpenSnackbar] = useState(false);

  const handleCloseSnackbar = () => {
    setOpenSnackbar(false);
  };

  const showError = (message) => {
    setError(message);
    setOpenSnackbar(true);
  };

  const handleFileUpload = async (event) => {
    const uploadedFile = event.target.files[0];
    if (!uploadedFile) return;

    // Check file type
    if (!uploadedFile.name.match(/\.(txt|pdf)$/i)) {
      showError('Please upload a text file (.txt) or PDF document (.pdf)');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);

      const response = await fetch('http://localhost:8000/simplify', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error processing the document');
      }

      const data = await response.json();
      setOriginalText(data.original);
      setSimplifiedText(data.simplified);
    } catch (error) {
      console.error('Error:', error);
      showError(error.message || 'Error processing the document');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!chatMessage.trim() || !simplifiedText) return;

    const newMessage = { text: chatMessage, sender: 'user' };
    setChatHistory([...chatHistory, newMessage]);
    setChatMessage('');
    setError('');

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: chatMessage,
          document_content: simplifiedText,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error sending message');
      }

      const data = await response.json();
      setChatHistory([...chatHistory, newMessage, { text: data.response, sender: 'bot' }]);
    } catch (error) {
      console.error('Error:', error);
      showError(error.message || 'Error sending message');
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom align="center" color="primary">
        Legal Document Simplifier
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <label htmlFor="file-upload">
              <Input
                id="file-upload"
                type="file"
                onChange={handleFileUpload}
                accept=".txt,.pdf"
                disabled={loading}
              />
              <Button
                variant="contained"
                component="span"
                startIcon={<CloudUploadIcon />}
                disabled={loading}
              >
                Upload Legal Document
              </Button>
            </label>
          </Paper>
        </Grid>

        {loading && (
          <Grid item xs={12} sx={{ textAlign: 'center' }}>
            <CircularProgress />
          </Grid>
        )}

        {simplifiedText && (
          <>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Original Document
                </Typography>
                <Box sx={{ maxHeight: '400px', overflow: 'auto' }}>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                    {originalText}
                  </Typography>
                </Box>
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Simplified Version
                </Typography>
                <Box sx={{ maxHeight: '400px', overflow: 'auto' }}>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                    {simplifiedText}
                  </Typography>
                </Box>
              </Paper>
            </Grid>

            <Grid item xs={12}>
              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Ask Questions About the Document
                </Typography>
                <Box sx={{ maxHeight: '300px', overflow: 'auto', mb: 2 }}>
                  {chatHistory.map((message, index) => (
                    <Box
                      key={index}
                      sx={{
                        display: 'flex',
                        justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                        mb: 1,
                      }}
                    >
                      <Paper
                        sx={{
                          p: 2,
                          maxWidth: '70%',
                          backgroundColor: message.sender === 'user' ? 'primary.light' : 'grey.100',
                          color: message.sender === 'user' ? 'white' : 'text.primary',
                        }}
                      >
                        <Typography variant="body1">{message.text}</Typography>
                      </Paper>
                    </Box>
                  ))}
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <TextField
                    fullWidth
                    variant="outlined"
                    placeholder="Type your question..."
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                    disabled={loading}
                  />
                  <Button
                    variant="contained"
                    onClick={handleSendMessage}
                    disabled={!chatMessage.trim() || loading}
                    endIcon={<SendIcon />}
                  >
                    Send
                  </Button>
                </Box>
              </Paper>
            </Grid>
          </>
        )}
      </Grid>

      <Snackbar
        open={openSnackbar}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default App; 