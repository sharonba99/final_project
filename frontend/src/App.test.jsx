import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';
import { vi } from 'vitest';
global.fetch = vi.fn();

global.fetch = jest.fn();

describe('URL Shortener Frontend Tests', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('renders the main heading', () => {
    render(<App />);
    const headingElement = screen.getByText(/Make it Short/i);
    expect(headingElement).toBeInTheDocument();
  });

  test('updates input value on change', () => {
    render(<App />);
    const input = screen.getByPlaceholderText(/google.com/i);
    fireEvent.change(input, { target: { value: 'https://github.com' } });
    expect(input.value).toBe('https://github.com');
  });

  test('successful URL shortening displays the result', async () => {
   
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ short_code: 'abc123' }),
    });

    render(<App />);
    const input = screen.getByPlaceholderText(/google.com/i);
    const button = screen.getByText(/Shorten URL/i);

   
    fireEvent.change(input, { target: { value: 'google.com' } });
    fireEvent.click(button);


    const resultLink = await screen.findByText(/\/r\/abc123/i);
    expect(resultLink).toBeInTheDocument();
    expect(screen.getByText(/Copy Link/i)).toBeInTheDocument();
  });

  test('handles API error correctly', async () => {

    fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ error: 'Invalid URL' }),
    });

    render(<App />);
    const input = screen.getByPlaceholderText(/google.com/i);
    const button = screen.getByText(/Shorten URL/i);

    fireEvent.change(input, { target: { value: 'invalid-url' } });
    fireEvent.click(button);

   
    const errorMsg = await screen.findByText(/Invalid URL. Please check the format/i);
    expect(errorMsg).toBeInTheDocument();
  });
});