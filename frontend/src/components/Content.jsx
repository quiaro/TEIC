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
      ) : presents ? (
        <div>
          <h2 className="content-title">Gift Ideas</h2>
          <div className="content-data">
            {presents.map((gift, index) => (
              <div key={index} className="gift-item">
                <h3>{gift.name}</h3>
                <p>{gift.description}</p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="content-message">
          <p>Select a team member and search.</p>
          <p className="content-hint">See the presents here.</p>
        </div>
      )}
    </div>
  );
}

export default Content;
