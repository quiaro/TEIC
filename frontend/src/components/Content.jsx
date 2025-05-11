import React from 'react';

function Content({ presents, loading }) {
  return (
    <div className="content">
      {loading && !presents ? (
        <div className="content-message">
          <div className="content-loading">
            <div className="content-loading-spinner"></div>
            <p>Fetching presents...</p>
          </div>
        </div>
      ) : (
        <div className="content-message"></div>
      )}
    </div>
  );
}

export default Content;
