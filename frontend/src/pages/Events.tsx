import {
  Box,
  Button,
  Card,
  CardBody,
  Heading,
  HStack,
  VStack,
  Text,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Spinner,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Select,
  Input,
  Flex,
  Spacer,
  Icon,
  useToast,
  ButtonGroup,
} from '@chakra-ui/react'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { FaDownload, FaFilter, FaChevronLeft, FaChevronRight } from 'react-icons/fa'
import { format } from 'date-fns'
import apiService from '../services/api'
import type { Event, RiskLevel } from '../types'

const ITEMS_PER_PAGE = 20

const Events = () => {
  const [currentPage, setCurrentPage] = useState(1)
  const [riskFilter, setRiskFilter] = useState<RiskLevel | ''>('')
  const [deviceFilter, setDeviceFilter] = useState('')
  const toast = useToast()

  const offset = (currentPage - 1) * ITEMS_PER_PAGE

  // Fetch events with pagination and filtering
  const {
    data: eventsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['events', currentPage, riskFilter, deviceFilter],
    queryFn: () =>
      apiService.getEvents(ITEMS_PER_PAGE, offset, {
        risk_level: riskFilter || undefined,
        device_id: deviceFilter || undefined,
      }),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const handleDownloadCSV = async (eventId: number) => {
    try {
      await apiService.downloadECGCSV(eventId)
      toast({
        title: 'Download Started',
        description: 'ECG CSV file download has started.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
    } catch (error) {
      toast({
        title: 'Download Failed',
        description: 'Failed to download ECG data. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    }
  }

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

  const totalPages = eventsData ? Math.ceil(eventsData.total / ITEMS_PER_PAGE) : 0

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const handleFilterChange = () => {
    setCurrentPage(1) // Reset to first page when filters change
    refetch()
  }

  if (error) {
    return (
      <Alert status="error">
        <AlertIcon />
        <AlertTitle>Error Loading Events</AlertTitle>
        <AlertDescription>
          Unable to load events data. Please check your connection and try again.
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <VStack spacing="6" align="stretch">
      {/* Page Header */}
      <Box>
        <Heading size="xl" mb="2">
          Event History
        </Heading>
        <Text color="gray.600">
          View and manage all MI detection events with filtering and export options
        </Text>
      </Box>

      {/* Filters */}
      <Card>
        <CardBody>
          <HStack spacing="4" align="end">
            <Box>
              <Text fontSize="sm" fontWeight="medium" mb="2">
                Risk Level
              </Text>
              <Select
                placeholder="All risk levels"
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value as RiskLevel | '')}
                width="200px"
              >
                <option value="HIGH">High Risk</option>
                <option value="MEDIUM">Medium Risk</option>
                <option value="LOW">Low Risk</option>
              </Select>
            </Box>

            <Box>
              <Text fontSize="sm" fontWeight="medium" mb="2">
                Device ID
              </Text>
              <Input
                placeholder="Filter by device..."
                value={deviceFilter}
                onChange={(e) => setDeviceFilter(e.target.value)}
                width="200px"
              />
            </Box>

            <Button
              leftIcon={<Icon as={FaFilter} />}
              onClick={handleFilterChange}
              colorScheme="medical"
              variant="outline"
            >
              Apply Filters
            </Button>
          </HStack>
        </CardBody>
      </Card>

      {/* Events Table */}
      <Card>
        <CardBody>
          <Flex align="center" mb="4">
            <Heading size="lg">Events</Heading>
            <Spacer />
            <Text color="gray.600" fontSize="sm">
              {eventsData ? `${eventsData.total} total events` : ''}
            </Text>
          </Flex>

          {isLoading ? (
            <Box textAlign="center" py="12">
              <Spinner size="lg" color="medical.500" />
              <Text mt="4" color="gray.600">Loading events...</Text>
            </Box>
          ) : !eventsData?.events.length ? (
            <Box textAlign="center" py="12">
              <Text color="gray.600">No events found matching your criteria</Text>
            </Box>
          ) : (
            <>
              <Box overflowX="auto">
                <Table variant="simple">
                  <Thead>
                    <Tr>
                      <Th>Device ID</Th>
                      <Th>Timestamp</Th>
                      <Th>Risk Score</Th>
                      <Th>Risk Level</Th>
                      <Th>Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {eventsData.events.map((event: Event) => (
                      <Tr key={event.id}>
                        <Td>
                          <Text fontFamily="mono" fontSize="sm">
                            {event.device_id}
                          </Text>
                        </Td>
                        <Td>
                          <Text fontSize="sm">
                            {format(new Date(event.timestamp), 'PPpp')}
                          </Text>
                        </Td>
                        <Td>
                          <Text
                            fontWeight="bold"
                            color={getRiskColor(event.risk_score)}
                          >
                            {(event.risk_score * 100).toFixed(1)}%
                          </Text>
                        </Td>
                        <Td>
                          <Badge colorScheme={getRiskBadgeColor(event.risk_level)}>
                            {event.risk_level}
                          </Badge>
                        </Td>
                        <Td>
                          <Button
                            size="sm"
                            leftIcon={<Icon as={FaDownload} />}
                            onClick={() => handleDownloadCSV(event.id)}
                            colorScheme="medical"
                            variant="outline"
                          >
                            Download ECG
                          </Button>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </Box>

              {/* Pagination */}
              {totalPages > 1 && (
                <Flex justify="center" align="center" mt="6" gap="2">
                  <Button
                    leftIcon={<Icon as={FaChevronLeft} />}
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    size="sm"
                    variant="outline"
                  >
                    Previous
                  </Button>

                  <ButtonGroup size="sm" variant="outline">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let pageNum: number
                      if (totalPages <= 5) {
                        pageNum = i + 1
                      } else if (currentPage <= 3) {
                        pageNum = i + 1
                      } else if (currentPage >= totalPages - 2) {
                        pageNum = totalPages - 4 + i
                      } else {
                        pageNum = currentPage - 2 + i
                      }

                      return (
                        <Button
                          key={pageNum}
                          onClick={() => handlePageChange(pageNum)}
                          colorScheme={currentPage === pageNum ? 'medical' : 'gray'}
                          variant={currentPage === pageNum ? 'solid' : 'outline'}
                        >
                          {pageNum}
                        </Button>
                      )
                    })}
                  </ButtonGroup>

                  <Button
                    rightIcon={<Icon as={FaChevronRight} />}
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    size="sm"
                    variant="outline"
                  >
                    Next
                  </Button>
                </Flex>
              )}

              <Text textAlign="center" fontSize="sm" color="gray.600" mt="4">
                Page {currentPage} of {totalPages} ({eventsData.total} total events)
              </Text>
            </>
          )}
        </CardBody>
      </Card>
    </VStack>
  )
}

export default Events