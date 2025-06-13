import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Zap, 
  Shield, 
  BarChart3, 
  Code, 
  Clock, 
  Users,
  ArrowRight,
  CheckCircle,
  Star
} from 'lucide-react';
import Layout from '../components/layout/Layout';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';

const HomePage: React.FC = () => {
  const features = [
    {
      icon: Zap,
      title: 'Высокая производительность',
      description: 'Быстрые ответы и минимальная задержка благодаря оптимизированной архитектуре',
    },
    {
      icon: Shield,
      title: 'Безопасность',
      description: 'Защищенные API-ключи, шифрование данных и контроль доступа',
    },
    {
      icon: BarChart3,
      title: 'Аналитика',
      description: 'Подробная статистика использования и мониторинг в реальном времени',
    },
    {
      icon: Code,
      title: 'Простая интеграция',
      description: 'REST API, SDK для популярных языков и подробная документация',
    },
    {
      icon: Clock,
      title: '99.9% Uptime',
      description: 'Надежная инфраструктура с высокой доступностью сервиса',
    },
    {
      icon: Users,
      title: 'Поддержка 24/7',
      description: 'Круглосуточная техническая поддержка и помощь разработчикам',
    },
  ];

  const stats = [
    { label: 'API запросов в день', value: '10M+' },
    { label: 'Активных разработчиков', value: '50K+' },
    { label: 'Поддерживаемых моделей', value: '25+' },
    { label: 'Стран использования', value: '120+' },
  ];

  const testimonials = [
    {
      name: 'Алексей Петров',
      role: 'CTO, TechStartup',
      content: 'LLM Gateway значительно упростил интеграцию ИИ в наш продукт. Отличная производительность и поддержка.',
      rating: 5,
    },
    {
      name: 'Мария Сидорова',
      role: 'Lead Developer, DataCorp',
      content: 'Простое API, подробная документация и стабильная работа. Рекомендую всем разработчикам.',
      rating: 5,
    },
    {
      name: 'Дмитрий Козлов',
      role: 'Founder, AI Solutions',
      content: 'Лучший сервис для работы с языковыми моделями. Гибкие тарифы и отличная аналитика.',
      rating: 5,
    },
  ];

  return (
    <Layout>
      {/* Hero Section */}
      <section className="relative bg-white overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <Badge variant="primary" className="mb-4">
              🚀 Новая версия API v1.0
            </Badge>
            
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Мощный API-шлюз для
              <span className="text-primary-600 block">языковых моделей</span>
            </h1>
            
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Интегрируйте передовые языковые модели в ваши приложения с помощью 
              простого и надежного API. Начните разработку уже сегодня.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register">
                <Button size="lg" className="w-full sm:w-auto">
                  Начать бесплатно
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              
              <Link to="/docs">
                <Button variant="outline" size="lg" className="w-full sm:w-auto">
                  Документация
                </Button>
              </Link>
            </div>
            
            <div className="mt-12">
              <p className="text-sm text-gray-500 mb-4">
                Доверяют более 50,000 разработчиков
              </p>
              
              <div className="flex justify-center items-center space-x-8 opacity-60">
                {/* Логотипы компаний */}
                <div className="text-2xl font-bold text-gray-400">TechCorp</div>
                <div className="text-2xl font-bold text-gray-400">DataLab</div>
                <div className="text-2xl font-bold text-gray-400">AI Startup</div>
                <div className="text-2xl font-bold text-gray-400">DevTeam</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="bg-primary-600 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-white mb-2">
                  {stat.value}
                </div>
                <div className="text-primary-100 text-sm md:text-base">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Почему выбирают LLM Gateway?
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Мы предоставляем все необходимые инструменты для успешной интеграции 
              и масштабирования ваших AI-приложений.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="text-center p-8 hover:shadow-lg transition-shadow">
                <div className="flex justify-center mb-4">
                  <div className="flex items-center justify-center w-12 h-12 bg-primary-100 rounded-lg">
                    <feature.icon className="h-6 w-6 text-primary-600" />
                  </div>
                </div>
                
                <h3 className="text-xl font-semibold text-gray-900 mb-3">
                  {feature.title}
                </h3>
                
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Code Example Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
                Простая интеграция за минуты
              </h2>
              
              <p className="text-lg text-gray-600 mb-8">
                Всего несколько строк кода для начала работы с мощными языковыми моделями. 
                Поддержка всех популярных языков программирования.
              </p>
              
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-gray-700">REST API с простой аутентификацией</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-gray-700">SDK для Python, JavaScript, Go</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-gray-700">Подробная документация и примеры</span>
                </div>
              </div>
              
              <div className="mt-8">
                <Link to="/docs">
                  <Button variant="primary">
                    Посмотреть документацию
                  </Button>
                </Link>
              </div>
            </div>
            
            <div>
              <Card className="bg-gray-900 text-green-400 font-mono text-sm overflow-hidden">
                <div className="p-6">
                  <div className="flex items-center space-x-2 mb-4">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-gray-400 ml-2">terminal</span>
                  </div>
                  
                  <pre className="text-green-400">
{`curl -X POST https://api.llmgateway.dev/v1/completions \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Напиши краткое описание ИИ",
    "max_tokens": 100,
    "temperature": 0.7
  }'`}
                  </pre>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Что говорят наши клиенты
            </h2>
            <p className="text-xl text-gray-600">
              Отзывы разработчиков и компаний, которые используют LLM Gateway
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="p-6">
                <div className="flex items-center mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="h-5 w-5 text-yellow-400 fill-current" />
                  ))}
                </div>
                
                <p className="text-gray-600 mb-4">
                  "{testimonial.content}"
                </p>
                
                <div>
                  <div className="font-semibold text-gray-900">
                    {testimonial.name}
                  </div>
                  <div className="text-sm text-gray-500">
                    {testimonial.role}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-primary-600">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Готовы начать разработку?
          </h2>
          
          <p className="text-xl text-primary-100 mb-8">
            Присоединяйтесь к тысячам разработчиков, которые уже используют 
            LLM Gateway для создания инновационных AI-приложений.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button 
                variant="secondary" 
                size="lg" 
                className="w-full sm:w-auto bg-white text-primary-600 hover:bg-gray-100"
              >
                Создать аккаунт
              </Button>
            </Link>
            
            <Link to="/playground">
              <Button 
                variant="outline" 
                size="lg" 
                className="w-full sm:w-auto border-white text-white hover:bg-white hover:text-primary-600"
              >
                Попробовать Playground
              </Button>
            </Link>
          </div>
          
          <p className="text-primary-200 text-sm mt-6">
            Бесплатный план включает 10,000 токенов в месяц. Без привязки карты.
          </p>
        </div>
      </section>
    </Layout>
  );
};

export default HomePage;