import React from 'react';

const MediaUploader = ({ onFilesChange, currentFiles }) => {
  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    onFilesChange(prev => [...prev, ...files]);
  };

  const removeFile = (index) => {
    onFilesChange(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="media-uploader">
      <input
        type="file"
        multiple
        onChange={handleFileChange}
        accept="image/*,video/*,audio/*"
        className="file-input"
      />
      
      {currentFiles.length > 0 && (
        <div className="uploaded-files">
          <h5>فایل‌های انتخاب‌شده:</h5>
          <div className="files-list">
            {currentFiles.map((file, index) => (
              <div key={index} className="file-item">
                <span>{file.name}</span>
                <button 
                  type="button" 
                  onClick={() => removeFile(index)}
                  className="remove-file-btn"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MediaUploader;