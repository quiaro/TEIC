import React, { useState } from 'react';

function Controls({ teamMembers, onSubmit, loading }) {
  const [hoveredMember, setHoveredMember] = useState(null);

  const handleSubmit = (teamMember) => {
    if (teamMember) {
      onSubmit(teamMember);
    }
  };

  return (
    <div className="controls">
      <div className="team-members-list">
        {teamMembers.map((teamMember) => (
          <div
            key={teamMember}
            className="team-member-row"
            onMouseEnter={() => setHoveredMember(teamMember)}
            onMouseLeave={() => setHoveredMember(null)}
          >
            <span className="team-member-name">{teamMember}</span>
            {hoveredMember === teamMember && (
              <button
                onClick={() => handleSubmit(teamMember)}
                disabled={loading}
                className="gift-button"
              >
                {loading ? (
                  <>
                    <span className="loading"></span>
                  </>
                ) : (
                  <>🎁</>
                )}
              </button>
            )}
          </div>
        ))}
      </div>
      <style jsx>{`
        .team-members-list {
          display: flex;
          flex-direction: column;
          gap: 6px;
          padding: 8px;
          width: 100%;
        }

        .team-member-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 8px 16px;
          border-radius: 6px;
          background: #f5f5f5;
          transition: background-color 0.2s ease;
          min-height: 52px;
        }

        .team-member-row:hover {
          background: #e8e8e8;
        }

        .team-member-name {
          font-size: 16px;
          font-weight: 500;
        }

        .gift-button {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          background: #007bff;
          color: white;
          cursor: pointer;
          transition: background-color 0.2s ease;
        }

        .gift-button:hover:not(:disabled) {
          background: #0056b3;
        }

        .gift-button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .loading {
          display: inline-block;
          width: 16px;
          height: 16px;
          border: 2px solid #ffffff;
          border-radius: 50%;
          border-top-color: transparent;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}

export default Controls;
