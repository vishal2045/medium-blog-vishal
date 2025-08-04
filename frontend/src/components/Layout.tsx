import {
  Box,
  Flex,
  Heading,
  HStack,
  Link,
  Spacer,
  Text,
  Badge,
  Icon,
  Container,
} from '@chakra-ui/react'
import { Link as RouterLink, useLocation } from 'react-router-dom'
import { FaHeartbeat, FaChartLine, FaList } from 'react-icons/fa'
import { ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Dashboard', icon: FaChartLine },
    { path: '/events', label: 'Events', icon: FaList },
  ]

  return (
    <Box minH="100vh">
      {/* Header */}
      <Box bg="white" shadow="sm" borderBottom="1px" borderColor="gray.200">
        <Container maxW="container.xl">
          <Flex h="16" alignItems="center">
            {/* Logo */}
            <HStack spacing="3">
              <Icon as={FaHeartbeat} w="8" h="8" color="medical.500" />
              <Heading size="lg" color="gray.800">
                Cardio360-Lite
              </Heading>
              <Badge colorScheme="medical" variant="subtle">
                Dashboard
              </Badge>
            </HStack>

            <Spacer />

            {/* Navigation */}
            <HStack spacing="8">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  as={RouterLink}
                  to={item.path}
                  display="flex"
                  alignItems="center"
                  px="3"
                  py="2"
                  rounded="md"
                  fontSize="sm"
                  fontWeight="medium"
                  color={location.pathname === item.path ? 'medical.600' : 'gray.600'}
                  bg={location.pathname === item.path ? 'medical.50' : 'transparent'}
                  _hover={{
                    color: 'medical.600',
                    bg: 'medical.50',
                    textDecoration: 'none',
                  }}
                  transition="all 0.2s"
                >
                  <Icon as={item.icon} mr="2" />
                  {item.label}
                </Link>
              ))}
            </HStack>
          </Flex>
        </Container>
      </Box>

      {/* Main Content */}
      <Box flex="1">
        <Container maxW="container.xl" py="8">
          {children}
        </Container>
      </Box>

      {/* Footer */}
      <Box bg="gray.800" color="white" py="4" mt="auto">
        <Container maxW="container.xl">
          <Flex alignItems="center" justify="space-between">
            <Text fontSize="sm">
              © 2024 Cardio360-Lite. Built for medical professionals.
            </Text>
            <Text fontSize="sm" color="gray.400">
              Emergency: Call 108 immediately for suspected MI
            </Text>
          </Flex>
        </Container>
      </Box>
    </Box>
  )
}

export default Layout