document.getElementById('uploadForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData();
  formData.append('image', e.target.image.files[0]);

  try {
    const response = await fetch('http://localhost:5000/upload', {
      method: 'POST',
      body: formData,
    });

    const result = await response.json();
    document.getElementById('result').innerText = JSON.stringify(result, null, 2);
  } catch (error) {
    document.getElementById('result').innerText = 'Error uploading file. Please try again.';
  }
});
