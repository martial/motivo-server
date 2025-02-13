// lib/services/db.js

/**
 * Base API URL from environment variables
 * @type {string}
 */
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5002';

/**
 * Service for handling database operations
 */
export class DbService {
  /**
   * Get all configurations from the database
   * @returns {Promise<Array>} Array of configurations
   */
  static async getAllConfigs() {
    try {
      const response = await fetch(`${API_URL}/api/conf`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching configs:', error);
      throw error;
    }
  }

  /**
   * Add a new configuration to the database
   * @param {Object} config Configuration object
   * @param {string} config.title Title of the configuration
   * @param {string} config.thumbnail Thumbnail URL
   * @param {string} config.type Type of configuration (vibe/reward/llm)
   * @param {Object} config.data Configuration data
   * @returns {Promise<Object>} Created configuration
   */
  static async addConfig({ title, thumbnail = '', type, data }) {
    try {
      const response = await fetch(`${API_URL}/api/conf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title,
          thumbnail,
          type,
          data
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error adding config:', error);
      throw error;
    }
  }

  /**
   * Update an existing configuration
   * @param {number} id Configuration ID
   * @param {Object} config Configuration object
   * @returns {Promise<Object>} Updated configuration
   */
  static async updateConfig(id, config) {
    try {
      const response = await fetch(`${API_URL}/api/conf/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error updating config:', error);
      throw error;
    }
  }

  /**
   * Delete a configuration
   * @param {number} id Configuration ID
   * @returns {Promise<void>}
   */
  static async deleteConfig(id) {
    try {
      const response = await fetch(`${API_URL}/api/conf/${id}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error deleting config:', error);
      throw error;
    }
  }
}

export default DbService;