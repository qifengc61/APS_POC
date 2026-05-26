import { createBrowserRouter, Navigate } from 'react-router-dom'
import AppLayout from '../layouts/AppLayout'
import ProcessRoutePage from '../pages/ProcessRoutePage'
import SchedulingPage from '../pages/SchedulingPage'
import ScheduledOrdersPage from '../pages/ScheduledOrdersPage'
import OrderPage from '../pages/OrderPage'
import QuickSchedulingPage from '../pages/QuickSchedulingPage'
import MaterialPage from '../pages/MaterialPage'
import BomPage from '../pages/BomPage'
import ProcessPage from '../pages/ProcessPage'
import ResourcePage from '../pages/ResourcePage'
import CalendarPage from '../pages/CalendarPage'
import IncomingOrderPage from '../pages/IncomingOrderPage'

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/quick-scheduling" replace /> },
      { path: 'materials', element: <MaterialPage /> },
      { path: 'bom', element: <BomPage /> },
      { path: 'processes', element: <ProcessPage /> },
      { path: 'process-routes', element: <ProcessRoutePage /> },
      { path: 'resources', element: <ResourcePage /> },
      { path: 'calendars', element: <CalendarPage /> },
      { path: 'incoming-orders', element: <IncomingOrderPage /> },
      { path: 'orders', element: <OrderPage /> },
      { path: 'quick-scheduling', element: <QuickSchedulingPage /> },
      { path: 'scheduling', element: <SchedulingPage /> },
      { path: 'scheduled-orders', element: <ScheduledOrdersPage /> },
    ],
  },
])

export default router
