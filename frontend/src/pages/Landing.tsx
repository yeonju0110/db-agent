import { useNavigate } from 'react-router-dom'

import { Header } from '../components/layout/Header'

export function Landing() {
  const navigate = useNavigate()
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <Header />

      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-blue-50 to-indigo-100 py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="mb-6 text-5xl font-bold text-gray-900">
              AI 기반 한국형 DB 모니터링
              <br />
              <span className="text-blue-600">SaaS 솔루션</span>
            </h1>
            <p className="mx-auto mb-8 max-w-3xl text-xl text-gray-600">
              자연어 쿼리와 실시간 이상 탐지로 누구나 쉽게 데이터베이스를 모니터링하고 즉시 대응할
              수 있는 스마트한 솔루션입니다
            </p>
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => navigate('/connections')}
                className="inline-flex cursor-pointer items-center justify-center rounded-lg bg-blue-600 px-6 py-3 text-base font-medium whitespace-nowrap text-white transition-colors hover:bg-blue-700 disabled:bg-blue-300"
              >
                무료로 시작하기
              </button>
              <button
                onClick={() => navigate('/dashboard')}
                className="inline-flex cursor-pointer items-center justify-center rounded-lg border border-gray-300 px-6 py-3 text-base font-medium whitespace-nowrap text-gray-700 transition-colors hover:bg-gray-50 disabled:bg-gray-100"
              >
                데모 보기
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-bold text-gray-900">
              왜 DBMonitor를 선택해야 할까요?
            </h2>
            <p className="text-lg text-gray-600">
              복잡한 DB 모니터링을 간단하고 스마트하게 만드는 핵심 기능들
            </p>
          </div>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg border border-gray-200 bg-white p-6 text-center shadow-sm transition-shadow hover:shadow-lg">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
                <i className="ri-brain-line text-2xl text-blue-600"></i>
              </div>
              <h3 className="mb-3 text-xl font-semibold text-gray-900">AI 기반 자연어 쿼리</h3>
              <p className="text-gray-600">복잡한 SQL 없이 자연어로 모니터링 지표를 설정하세요</p>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-6 text-center shadow-sm transition-shadow hover:shadow-lg">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
                <i className="ri-time-line text-2xl text-blue-600"></i>
              </div>
              <h3 className="mb-3 text-xl font-semibold text-gray-900">실시간 모니터링</h3>
              <p className="text-gray-600">1시간 단위로 자동 실행되는 실시간 데이터 모니터링</p>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-6 text-center shadow-sm transition-shadow hover:shadow-lg">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
                <i className="ri-alert-line text-2xl text-blue-600"></i>
              </div>
              <h3 className="mb-3 text-xl font-semibold text-gray-900">스마트 이상 감지</h3>
              <p className="text-gray-600">자동으로 이상치를 감지하고 즉시 알림을 전송합니다</p>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-6 text-center shadow-sm transition-shadow hover:shadow-lg">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
                <i className="ri-dashboard-line text-2xl text-blue-600"></i>
              </div>
              <h3 className="mb-3 text-xl font-semibold text-gray-900">직관적 대시보드</h3>
              <p className="text-gray-600">한눈에 보기 쉬운 시각화와 상세한 분석 정보 제공</p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="bg-gray-50 py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-bold text-gray-900">실제 사용자들의 이야기</h2>
            <p className="text-lg text-gray-600">
              다양한 직군의 전문가들이 DBMonitor로 업무 효율성을 높이고 있습니다
            </p>
          </div>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            <div className="rounded-lg border border-gray-200 bg-white p-6 text-center shadow-sm">
              <img
                alt="정하늘"
                className="mx-auto mb-4 h-24 w-24 rounded-full object-cover object-top"
                src="https://readdy.ai/api/search-image?query=Professional%20Korean%20female%20product%20manager%20in%20modern%20office%20setting%2C%20confident%20business%20woman%20with%20short%20hair%20wearing%20business%20casual%20attire%2C%20clean%20corporate%20background%20with%20soft%20lighting%2C%20professional%20headshot%20style&width=300&height=300&seq=persona1&orientation=squarish"
              />
              <h3 className="mb-1 text-xl font-semibold text-gray-900">정하늘</h3>
              <p className="mb-4 font-medium text-blue-600">프로덕트 매니저</p>
              <blockquote className="text-gray-600 italic">
                "제품에 문제가 생기면 누가 뭘 해야 할지 바로 알 수 있어서 좋아요"
              </blockquote>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-6 text-center shadow-sm">
              <img
                alt="김도현"
                className="mx-auto mb-4 h-24 w-24 rounded-full object-cover object-top"
                src="https://readdy.ai/api/search-image?query=Professional%20Korean%20male%20backend%20developer%20in%20modern%20tech%20office%2C%20young%20programmer%20with%20glasses%20wearing%20casual%20shirt%2C%20clean%20workspace%20with%20monitors%20in%20background%2C%20professional%20portrait%20style&width=300&height=300&seq=persona2&orientation=squarish"
              />
              <h3 className="mb-1 text-xl font-semibold text-gray-900">김도현</h3>
              <p className="mb-4 font-medium text-blue-600">백엔드 개발자</p>
              <blockquote className="text-gray-600 italic">
                "내가 만든 기능이 잘 돌아가는지 실시간으로 확인할 수 있어 안심돼요"
              </blockquote>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-6 text-center shadow-sm">
              <img
                alt="이서영"
                className="mx-auto mb-4 h-24 w-24 rounded-full object-cover object-top"
                src="https://readdy.ai/api/search-image?query=Professional%20Korean%20female%20data%20analyst%20working%20with%20charts%20and%20graphs%2C%20young%20woman%20with%20long%20hair%20in%20modern%20office%20environment%2C%20data%20visualization%20screens%20in%20background%2C%20professional%20business%20portrait&width=300&height=300&seq=persona3&orientation=squarish"
              />
              <h3 className="mb-1 text-xl font-semibold text-gray-900">이서영</h3>
              <p className="mb-4 font-medium text-blue-600">데이터 분석가</p>
              <blockquote className="text-gray-600 italic">
                "SQL 없이도 자연어로 쉽게 데이터를 분석할 수 있어 정말 편해요"
              </blockquote>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-blue-600 py-20">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="mb-4 text-3xl font-bold text-white">지금 바로 시작해보세요</h2>
          <p className="mb-8 text-xl text-blue-100">
            5분만에 설정 완료하고 실시간 DB 모니터링을 경험해보세요
          </p>
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => navigate('/connections')}
              className="inline-flex cursor-pointer items-center justify-center rounded-lg bg-white px-6 py-3 text-base font-medium whitespace-nowrap text-blue-600 transition-colors hover:bg-gray-100"
            >
              무료 체험 시작
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="inline-flex cursor-pointer items-center justify-center rounded-lg border border-white px-6 py-3 text-base font-medium whitespace-nowrap text-white transition-colors hover:bg-white hover:text-blue-600"
            >
              문의하기
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
            <div className="col-span-1 md:col-span-2">
              <h3
                className="mb-4 text-2xl font-bold text-white"
                style={{ fontFamily: 'Pacifico, serif' }}
              >
                DBMonitor
              </h3>
              <p className="mb-4 text-gray-400">
                AI 기반 자연어 쿼리와 실시간 이상 탐지로 누구나 쉽게 데이터베이스를 모니터링할 수
                있는 한국형 SaaS 솔루션
              </p>
            </div>
            <div>
              <h4 className="mb-4 font-semibold text-white">제품</h4>
              <ul className="space-y-2 text-gray-400">
                <li>
                  <a href="#" className="cursor-pointer transition-colors hover:text-white">
                    기능 소개
                  </a>
                </li>
                <li>
                  <a href="#" className="cursor-pointer transition-colors hover:text-white">
                    요금제
                  </a>
                </li>
                <li>
                  <a href="#" className="cursor-pointer transition-colors hover:text-white">
                    API 문서
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="mb-4 font-semibold text-white">지원</h4>
              <ul className="space-y-2 text-gray-400">
                <li>
                  <a href="#" className="cursor-pointer transition-colors hover:text-white">
                    도움말
                  </a>
                </li>
                <li>
                  <a href="#" className="cursor-pointer transition-colors hover:text-white">
                    문의하기
                  </a>
                </li>
                <li>
                  <a href="#" className="cursor-pointer transition-colors hover:text-white">
                    상태 페이지
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-8 flex items-center justify-between border-t border-gray-800 pt-8">
            <p className="text-sm text-gray-400">© 2025 DBMonitor. All rights reserved.</p>
            <a
              href="https://github.com/yeonju0110"
              className="cursor-pointer text-sm text-gray-400 transition-colors hover:text-white"
            >
              Yeonju Jo
            </a>
          </div>
        </div>
      </footer>
    </div>
  )
}
