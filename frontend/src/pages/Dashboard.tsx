import {
  Box,
  Grid,
  Heading,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Card,
  CardBody,
  Text,
  Badge,
  VStack,
  HStack,
  Icon,
  Spinner,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
} from '@chakra-ui/react'
import { useQuery } from '@tanstack/react-query'
import { FaExclamationTriangle, FaHeartbeat, FaCalendarDay, FaChartLine } from 'react-icons/fa'
import { format } from 'date-fns'
import apiService from '../services/api'
import type { Event } from '../types'

const Dashboard = () => {
  // Fetch dashboard statistics
  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: apiService.getDashboardStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Fetch recent events
  const {
    data: recentEvents,
    isLoading: eventsLoading,
    error: eventsError,
  } = useQuery({
    queryKey: ['recent-events'],
    queryFn: () => apiService.getEvents(10, 0), // Get 10 most recent events
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  const getRiskColor = (riskScore: number) => {
    if (riskScore > 0.8) return 'alert.500'
    if (riskScore > 0.5) return 'yellow.500'
    return 'green.500'
  }

  const getRiskBadgeColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'HIGH': return 'red'
      case 'MEDIUM': return 'yellow'
      case 'LOW': return 'green'
      default: return 'gray'
    }
  }

  if (statsError || eventsError) {
    return (
      <Alert status="error">
        <AlertIcon />
        <AlertTitle>Dashboard Error</AlertTitle>
        <AlertDescription>
          Unable to load dashboard data. Please check your connection and try again.
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <VStack spacing="8" align="stretch">
      {/* Page Header */}
      <Box>
        <Heading size="xl" mb="2">
          MI Detection Dashboard
        </Heading>
        <Text color="gray.600">
          Real-time monitoring of cardiac events and risk assessments
        </Text>
      </Box>

      {/* Statistics Cards */}
      <Grid templateColumns={{ base: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' }} gap="6">
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>
                <HStack>
                  <Icon as={FaHeartbeat} color="medical.500" />
                  <Text>Total Events</Text>
                </HStack>
              </StatLabel>
              <StatNumber>
                {statsLoading ? <Spinner size="sm" /> : stats?.total_events || 0}
              </StatNumber>
              <StatHelpText>All time</StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>
                <HStack>
                  <Icon as={FaExclamationTriangle} color="alert.500" />
                  <Text>High Risk Events</Text>
                </HStack>
              </StatLabel>
              <StatNumber color="alert.500">
                {statsLoading ? <Spinner size="sm" /> : stats?.high_risk_events || 0}
              </StatNumber>
              <StatHelpText>Risk score > 0.8</StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>
                <HStack>
                  <Icon as={FaCalendarDay} color="medical.500" />
                  <Text>Today's Events</Text>
                </HStack>
              </StatLabel>
              <StatNumber>
                {statsLoading ? <Spinner size="sm" /> : stats?.events_today || 0}
              </StatNumber>
              <StatHelpText>
                <StatArrow type="increase" />
                New today
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>
                <HStack>
                  <Icon as={FaChartLine} color="medical.500" />
                  <Text>Avg Risk Score</Text>
                </HStack>
              </StatLabel>
              <StatNumber>
                {statsLoading ? (
                  <Spinner size="sm" />
                ) : (
                  (stats?.average_risk_score || 0).toFixed(3)
                )}
              </StatNumber>
              <StatHelpText>Overall average</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </Grid>

      {/* Recent Events */}
      <Card>
        <CardBody>
          <Heading size="lg" mb="4">
            Recent Events
          </Heading>
          
          {eventsLoading ? (
            <Box textAlign="center" py="8">
              <Spinner size="lg" color="medical.500" />
              <Text mt="4" color="gray.600">Loading recent events...</Text>
            </Box>
          ) : !recentEvents?.events.length ? (
            <Box textAlign="center" py="8">
              <Text color="gray.600">No events found</Text>
            </Box>
          ) : (
            <VStack spacing="4" align="stretch">
              {recentEvents.events.map((event: Event) => (
                <Box
                  key={event.id}
                  p="4"
                  border="1px"
                  borderColor="gray.200"
                  borderRadius="md"
                  _hover={{ bg: 'gray.50' }}
                  transition="background-color 0.2s"
                >
                  <HStack justify="space-between" align="start">
                    <VStack align="start" spacing="1">
                      <HStack>
                        <Text fontWeight="semibold">Device: {event.device_id}</Text>
                        <Badge colorScheme={getRiskBadgeColor(event.risk_level)}>
                          {event.risk_level}
                        </Badge>
                      </HStack>
                      <Text fontSize="sm" color="gray.600">
                        {format(new Date(event.timestamp), 'PPpp')}
                      </Text>
                    </VStack>
                    
                    <VStack align="end" spacing="1">
                      <Text
                        fontWeight="bold"
                        fontSize="lg"
                        color={getRiskColor(event.risk_score)}
                      >
                        {(event.risk_score * 100).toFixed(1)}%
                      </Text>
                      <Text fontSize="xs" color="gray.500">
                        Risk Score
                      </Text>
                    </VStack>
                  </HStack>
                </Box>
              ))}
            </VStack>
          )}
        </CardBody>
      </Card>
    </VStack>
  )
}

export default Dashboard