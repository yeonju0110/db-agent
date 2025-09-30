import { Link, useLocation } from 'react-router-dom'

export function Header() {
  const location = useLocation()
  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 bg-white">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Link to="/">
                <h1
                  className="text-2xl font-bold text-blue-600"
                  style={{ fontFamily: 'Pacifico, serif' }}
                >
                  DBMonitor
                </h1>
              </Link>
            </div>
          </div>
          <nav className="hidden space-x-8 md:flex">
            <Link
              to="/dashboard"
              className={`cursor-pointer px-3 py-2 text-sm font-medium transition-colors ${
                location.pathname === '/dashboard'
                  ? 'text-blue-600'
                  : 'text-gray-700 hover:text-blue-600'
              }`}
            >
              대시보드
            </Link>
            <Link
              to="/connections"
              className={`cursor-pointer px-3 py-2 text-sm font-medium transition-colors ${
                location.pathname === '/connections'
                  ? 'text-blue-600'
                  : 'text-gray-700 hover:text-blue-600'
              }`}
            >
              DB 연결 관리
            </Link>
            <Link
              to="/setup"
              className={`cursor-pointer px-3 py-2 text-sm font-medium transition-colors ${
                location.pathname === '/setup'
                  ? 'text-blue-600'
                  : 'text-gray-700 hover:text-blue-600'
              }`}
            >
              모니터링 설정
            </Link>
            <Link
              to="/dashboard"
              className="cursor-pointer px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:text-blue-600"
            >
              알림 관리
            </Link>
          </nav>
          <div className="hidden items-center space-x-4 md:flex">
            <Link
              to="/dashboard"
              className="cursor-pointer text-gray-400 hover:text-gray-600"
              title="알림 관리"
            >
              <i className="ri-notification-3-line text-xl"></i>
            </Link>
            <Link
              to="/dashboard"
              className="flex items-center space-x-2 rounded-lg px-2 py-1 transition-colors hover:bg-gray-50"
              title="사용자 설정"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600">
                <span className="text-sm font-medium text-white">정</span>
              </div>
              <span className="text-sm font-medium text-gray-700">정하늘</span>
            </Link>
          </div>
          <div className="md:hidden">
            <button className="cursor-pointer text-gray-400 hover:text-gray-600" title="메뉴">
              <i className="ri-menu-line text-xl"></i>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
