import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  return {
    server: {
      host: env.FRONTEND_HOST || '127.0.0.1',
      port: Number(env.FRONTEND_PORT || 5173),
      strictPort: true,
      proxy: {'/api': {target:env.BACKEND_ORIGIN || 'http://127.0.0.1:8000',changeOrigin:false}},
    },
  };
});
